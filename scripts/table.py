#!/usr/bin/env python3
"""Table runner: plays a tabletop session on a GitHub Issue, turn by turn, with any mix of
AI agents and people in the GM's and players' seats.

    python scripts/table.py run    <table.json> [--step] [--turns N] [--dry-run]
    python scripts/table.py status <table.json>

Every comment on the Issue starts with its author's tag: the GM's ([KP] in Call of Cthulhu)
or the character's name ([Henry Ashworth]). The GM ends each comment with a hidden turn marker:

    <!-- turn: Name A, Name B -->   those characters act next, in that order
    <!-- turn: all -->              every player
    <!-- end -->                    the session is over

(Spanish also works: <!-- turno: ... -->, <!-- turno: todos -->, <!-- fin -->.) Without a
marker, every player acts. Once everyone called on has answered, it is the GM's turn again.

Seats are AI agents run through a command line (runner "hermes", "claude" or any "command")
or people (runner "human"), who comment on the Issue from GitHub or type their turn here.
See the README, "Table runner", for the table file and the ways to play.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

MARKER_RE = re.compile(r"<!--\s*(?:(?:turn|turno)\s*:\s*(?P<who>[^>]*?)|(?P<end>end|fin))\s*-->", re.I)
ALL_WORDS = {"all", "todos", "everyone", "*", ""}
TAG_RE = re.compile(r"\s*\[([^\]\n]{1,60})\]")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
HERMES_SESSION_RE = re.compile(r"session_id:\s*(\S+)")

DEFAULT_PROMPTS = {
    "gm_intro": (
        "You are the game master of the tabletop session on GitHub Issue #{issue} of {repo}, "
        "tagged [{tag}]. Follow your GM skill. The table's opening (Issue body and first replies, "
        "if any) is below."
    ),
    "gm_turn": (
        "Your turn as GM on Issue #{issue} of {repo}. New since your last turn:\n\n{new}\n\n"
        "Rule on what the players did (roll dice in the open) and {post_how}. "
        "One beat, ending where the players can act, with the turn marker as the last line: "
        "<!-- turn: Name, ... -->, <!-- turn: all --> or <!-- end -->. Players: {players}."
    ),
    "player_intro": (
        "You play {name} at the tabletop session on GitHub Issue #{issue} of {repo}. Follow your "
        "player skill: play only {name}, in character, in the table's language; never narrate "
        "outcomes or speak for the GM's characters. {sheet_line}"
        "The table so far (the Issue body, then the latest replies):\n\n{new}\n\n"
        "Now {post_how}."
    ),
    "player_turn": (
        "Your turn as {name} on Issue #{issue} of {repo}. New since your last turn:\n\n{new}\n\n"
        "Answer the GM's latest reply, where things stand now: {post_how}."
    ),
}
POST_HOW = {
    "agent": "post ONE comment on the Issue yourself, starting with [{tag}]",
    "cli": ("reply with ONLY the text of your comment, starting with [{tag}], and nothing else: "
            "the table runner posts it for you"),
}


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def tag_of(body):
    m = TAG_RE.match(body or "")
    return m.group(1).strip() if m else None


def norm(name):
    return re.sub(r"\s+", " ", name or "").strip().lower()


# ---------- GitHub (through the gh CLI) ----------

class Table:
    def __init__(self, repo, issue):
        self.repo, self.issue = repo, issue

    def _gh(self, *args, input=None):
        return subprocess.run(["gh", *args], input=input, capture_output=True, text=True, check=True).stdout

    def body(self):
        return json.loads(self._gh("api", f"repos/{self.repo}/issues/{self.issue}", "--jq", ".body | @json"))

    def comments(self):
        """[(number, body, url)], replies numbered from 1."""
        out = self._gh("api", f"repos/{self.repo}/issues/{self.issue}/comments?per_page=100", "--paginate",
                       "--jq", ".[] | [.body, .html_url] | @json")
        rows = [json.loads(line) for line in out.splitlines() if line.strip()]
        return [(i + 1, b or "", u) for i, (b, u) in enumerate(rows)]

    def post(self, body):
        url = self._gh("issue", "comment", str(self.issue), "--repo", self.repo, "--body-file", "-", input=body)
        return url.strip()

    def download(self, path, dest):
        data = subprocess.run(["gh", "api", f"repos/{self.repo}/contents/{path}",
                               "-H", "Accept: application/vnd.github.raw"],
                              capture_output=True, check=True).stdout
        dest.write_bytes(data)
        return dest


# ---------- turn logic ----------

class Seats:
    def __init__(self, cfg):
        self.gm = next(s for s in cfg["seats"] if s.get("role") == "gm")
        self.gm.setdefault("name", cfg.get("gm_tag", "GM"))
        self.players = [s for s in cfg["seats"] if s.get("role") != "gm"]
        self.by_name = {norm(s["name"]): s for s in cfg["seats"]}

    def find(self, name):
        n = norm(name)
        if n in self.by_name:
            return self.by_name[n]
        hits = [s for k, s in self.by_name.items() if s is not self.gm and (n in k or k in n)]
        return hits[0] if len(hits) == 1 else None


def whose_turn(comments, seats):
    """('end', None) | ('gm', None) | ('player', seat): computed from the thread alone, so the
    runner can stop and resume at any point."""
    gm_tag = norm(seats.gm["name"])
    last_gm = max((n for n, b, _ in comments if norm(tag_of(b)) == gm_tag), default=None)
    if last_gm is None:
        return "gm", None
    body = comments[last_gm - 1][1]
    m = None
    for m in MARKER_RE.finditer(body):
        pass  # the last marker wins
    if m and m.group("end"):
        return "end", None
    who = (m.group("who") or "").strip() if m else ""
    if norm(who) in ALL_WORDS:
        called = list(seats.players)
    else:
        called = [s for s in (seats.find(w) for w in who.split(",")) if s] or list(seats.players)
    answered = {norm(tag_of(b)) for n, b, _ in comments if n > last_gm}
    for seat in called:
        if norm(seat["name"]) not in answered:
            return "player", seat
    return "gm", None


# ---------- runners ----------

def render_replies(comments, start, limit_chars):
    """Replies from number `start` on, newest kept whole when over the size limit."""
    parts = [f"--- reply {n} ---\n{b.strip()}" for n, b, _ in comments if n >= start]
    out, size = [], 0
    for p in reversed(parts):
        if size + len(p) > limit_chars and out:
            out.append(f"[… {len(parts) - len(out)} earlier replies omitted: read them on the Issue …]")
            break
        out.append(p)
        size += len(p)
    return "\n\n".join(reversed(out)) or "(no new replies)"


def new_images(table, comments, start, cache):
    """Local copies of the table repository's images shown in replies since `start`."""
    paths = []
    for n, b, _ in comments:
        if n < start:
            continue
        for url in IMAGE_RE.findall(b):
            m = (re.match(rf"https://github\.com/{re.escape(table.repo)}/(?:blob|raw)/[^/]+/([^?#]+)", url)
                 or re.match(rf"https://raw\.githubusercontent\.com/{re.escape(table.repo)}/[^/]+/([^?#]+)", url))
            if m:
                rel = m.group(1)
                dest = cache / rel.replace("/", "__")
                if dest in paths:
                    continue
                try:
                    if not dest.exists():
                        table.download(rel, dest)
                    paths.append(dest)
                except subprocess.CalledProcessError:
                    log(f"  couldn't download {rel}")
    return paths


def one_image(paths, cache):
    """Hermes takes one image per message: stack several into one when Pillow is available."""
    if len(paths) <= 1:
        return paths[0] if paths else None
    try:
        from PIL import Image
    except ImportError:
        return paths[-1]
    imgs = [Image.open(p).convert("RGB") for p in paths]
    width = max(i.width for i in imgs)
    imgs = [i.resize((width, int(i.height * width / i.width))) if i.width != width else i for i in imgs]
    sheet = Image.new("RGB", (width, sum(i.height for i in imgs) + 20 * (len(imgs) - 1)), "white")
    y = 0
    for i in imgs:
        sheet.paste(i, (0, y))
        y += i.height + 20
    dest = cache / f"stack-{int(time.time())}.jpg"
    sheet.save(dest, quality=85)
    return dest


def run_agent(seat, prompt, image, state, dry_run):
    """Run one agent turn; returns its final answer. Keeps the agent's session in state."""
    key = f"session:{seat['name']}"
    runner = seat.get("runner", "hermes")
    workdir = Path(os.path.expanduser(seat.get("workdir", "~")))
    resume = state.get(key)
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    if runner == "hermes":
        cmd = ["hermes"] + (["-p", seat["profile"]] if seat.get("profile") else []) + ["chat", "-Q"]
        for flag, field in (("--provider", "provider"), ("-m", "model"), ("--reasoning", "reasoning"),
                            ("-t", "toolsets"), ("--max-turns", "max_turns")):
            if seat.get(field):
                cmd += [flag, str(seat[field])]
        if resume:
            cmd += ["--resume", resume]
        elif seat.get("skills"):
            cmd += ["-s", seat["skills"]]
        if image:
            cmd += ["--image", str(image)]
        cmd += ["--query-file", prompt_file]
        stdin = None
    elif runner == "claude":
        cmd = ["claude", "-p", "--output-format", "json"]
        if seat.get("model"):
            cmd += ["--model", seat["model"]]
        if resume:
            cmd += ["--resume", resume]
        cmd += seat.get("args", [])
        if image:
            prompt += f"\n\n(Image shown in the new replies: {image})"
        stdin = prompt
    elif runner == "command":
        cmd = [os.path.expanduser(a) for a in seat["command"]]
        if image:
            prompt += f"\n\n(Image shown in the new replies: {image})"
        stdin = prompt
    else:
        raise SystemExit(f"Unknown runner for {seat['name']}: {runner}")

    log(f"→ {seat['name']} ({runner}{' ' + seat['model'] if seat.get('model') else ''})")
    if dry_run:
        print("   ", shlex.join(cmd), f"< {len(prompt)} chars" + (f", image {image}" if image else ""))
        print("   ", prompt[:400].replace("\n", "\n    "), "…" if len(prompt) > 400 else "")
        os.unlink(prompt_file)
        return ""
    t0 = time.time()
    proc = subprocess.run(cmd, input=stdin, capture_output=True, text=True, cwd=workdir,
                          timeout=seat.get("timeout", 1800))
    os.unlink(prompt_file)
    out = proc.stdout
    if runner == "hermes":
        ids = HERMES_SESSION_RE.findall(out + proc.stderr)
        if ids:
            state[key] = ids[-1]
        out = HERMES_SESSION_RE.sub("", out).strip()
    elif runner == "claude":
        try:
            data = json.loads(out)
            state[key] = data.get("session_id", resume)
            out = data.get("result", "")
        except json.JSONDecodeError:
            pass
    if proc.returncode != 0:
        log(f"  {seat['name']} exited with {proc.returncode}: {(proc.stderr or out)[-500:]}")
    log(f"← {seat['name']} in {time.time() - t0:.0f}s")
    return out.strip()


def as_comment(answer, tag):
    """The comment in an agent's answer: from its [Tag] on, without code fences around it."""
    text = re.sub(r"^```\w*\n|\n```$", "", answer.strip())
    i = text.find(f"[{tag}]")
    return text[i:].strip() if i >= 0 else ""


def human_from_terminal(seat, comments, state):
    """Show what is new to a person playing at this terminal, then read their turn."""
    seen = state.get(f"seen:{seat['name']}", 0)
    for n, b, url in comments:
        if n > seen and norm(tag_of(b)) != norm(seat["name"]):
            print(f"\n──── reply {n} · {url}\n{b.strip()}\n")
    print(f"Your turn, {seat['name']}. Type your turn; finish with an empty line "
          f"(an empty turn quits).")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip() and lines:
            break
        if not line.strip() and not lines:
            return None
        lines.append(line)
    text = "\n".join(lines).strip()
    return text if text.startswith(f"[{seat['name']}]") else f"[{seat['name']}] {text}"


# ---------- main loop ----------

def pause(step, label):
    if not step:
        return True
    try:
        answer = input(f"\nNext: {label}. [Enter] go on · q quit › ").strip().lower()
    except EOFError:
        return False
    return answer not in ("q", "quit", "exit")


def run(cfg_path, step=False, turns=None, dry_run=False):
    cfg = json.loads(cfg_path.read_text())
    state_path = cfg_path.with_name(cfg_path.stem + ".state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    cache = Path(os.path.expanduser(cfg.get("cache_dir", "~/.cache/ai-tabletop"))) / cfg_path.stem
    cache.mkdir(parents=True, exist_ok=True)

    def save():
        if not dry_run:
            state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    table = Table(cfg["repo"], cfg["issue"])
    prompts = {**DEFAULT_PROMPTS, **cfg.get("prompts", {})}
    limit = cfg.get("context_chars", 40000)
    intro_replies = cfg.get("intro_replies", 12)
    poll = cfg.get("poll_seconds", 30)
    done = 0

    while turns is None or done < turns:
        cfg = json.loads(cfg_path.read_text())  # edits apply from the next turn on
        seats = Seats(cfg)
        comments = table.comments()
        kind, seat = whose_turn(comments, seats)
        if kind == "end":
            log("The GM closed the session (<!-- end -->).")
            break
        seat = seat or seats.gm
        name = seat["name"]
        runner = seat.get("runner", "hermes")
        total = len(comments)

        if runner == "human":
            if seat.get("input") == "terminal":
                text = human_from_terminal(seat, comments, state)
                if text is None:
                    break
                url = table.post(text)
                log(f"posted {url}")
                state[f"seen:{name}"] = total + 1
                save()
            else:
                log(f"Waiting for {name} to comment on {cfg['repo']}#{cfg['issue']} (every {poll}s; Ctrl+C stops)…")
                while table.comments()[-1:] == comments[-1:]:
                    time.sleep(poll)
            continue

        if not pause(step, f"{name} ({runner}{' · ' + seat['model'] if seat.get('model') else ''})"):
            break

        role = "gm" if seat is seats.gm else "player"
        posts = seat.get("posts", "agent" if role == "gm" else "cli")
        seen = state.get(f"seen:{name}")
        first = not state.get(f"session:{name}")
        if first or seen is None:
            start = 1 if role == "gm" else max(1, total - intro_replies + 1)
            new = f"--- Issue body ---\n{table.body().strip()}\n\n" + render_replies(comments, start, limit)
        else:
            start = seen + 1
            new = render_replies(comments, start, limit)
        fields = dict(
            issue=cfg["issue"], repo=cfg["repo"], tag=name, name=name, new=new,
            players=", ".join(p["name"] for p in seats.players),
            sheet_line=(f"Your character sheet: {seat['sheet']} (read it with book_read, or ask the GM). "
                        if seat.get("sheet") else ""),
        )
        fields["post_how"] = POST_HOW[posts].format(**fields)
        template = prompts[f"{role}_intro"] if first else prompts[f"{role}_turn"]
        prompt = template.format(**fields)
        if first and role == "gm":
            prompt += "\n\n" + prompts["gm_turn"].format(**fields)
        if seat.get("instructions"):
            prompt += "\n\n" + seat["instructions"]
        if cfg.get("instructions", {}).get(role):
            prompt += "\n\n" + cfg["instructions"][role]
        images = new_images(table, comments, start, cache) if seat.get("images", True) else []
        image = one_image(images, cache)

        posted, answer = False, ""
        for attempt in range(2):
            answer = run_agent(seat, prompt, image, state, dry_run)
            save()
            if dry_run:
                posted = True
                break
            if posts == "cli":
                comment = as_comment(answer, name)
                if comment:
                    log(f"posted {table.post(comment)}")
                    posted = True
                    break
                prompt = (f"Your answer had no comment starting with [{name}]. Reply again with ONLY the "
                          f"comment. If you can't follow what is happening at the table, say so in it, "
                          f"out of character, instead of guessing.")
            else:
                after = table.comments()
                mine = [u for n, b, u in after if n > total and norm(tag_of(b)) == norm(name)]
                if mine:
                    log(f"posted {mine[-1]}")
                    posted = True
                    break
                prompt = (f"I don't see your comment on Issue #{cfg['issue']}. Post it now, starting with "
                          f"[{name}]. If something stops you, say what.")
            log(f"  {name} didn't post; asking once more")
        if not posted:
            log(f"{name} didn't post. Stopping here: check its last answer above, then run again.")
            print(answer[-2000:])
            sys.exit(1)
        state[f"seen:{name}"] = len(table.comments()) if not dry_run else total
        save()
        done += 1
        if dry_run:
            break


def status(cfg_path):
    cfg = json.loads(cfg_path.read_text())
    seats = Seats(cfg)
    table = Table(cfg["repo"], cfg["issue"])
    comments = table.comments()
    kind, seat = whose_turn(comments, seats)
    state_path = cfg_path.with_name(cfg_path.stem + ".state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    print(f"{cfg['repo']}#{cfg['issue']}: {len(comments)} replies")
    print("Next:", "session over" if kind == "end" else (seat or seats.gm)["name"])
    for s in cfg["seats"]:
        what = s.get("runner", "hermes") + (f" · {s['model']}" if s.get("model") else "")
        print(f"  {s.get('role', 'player'):6} {s['name']:20} {what:40} "
              f"seen {state.get('seen:' + s['name'], '-')}, session {state.get('session:' + s['name'], '-')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="play turns until the GM ends the session (or --turns)")
    r.add_argument("table", type=Path, help="table file (JSON)")
    r.add_argument("--step", action="store_true", help="ask before each AI turn, to read along at your pace")
    r.add_argument("--turns", type=int, help="stop after this many AI turns")
    r.add_argument("--dry-run", action="store_true", help="show the next AI turn's command and prompt, run nothing")
    s = sub.add_parser("status", help="whose turn it is, and each seat's session")
    s.add_argument("table", type=Path)
    args = ap.parse_args()
    try:
        if args.cmd == "run":
            run(args.table.resolve(), args.step, args.turns, args.dry_run)
        else:
            status(args.table.resolve())
    except KeyboardInterrupt:
        print()
        log("Stopped. Run it again to go on where it left off.")


if __name__ == "__main__":
    main()
