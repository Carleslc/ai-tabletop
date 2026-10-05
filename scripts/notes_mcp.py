#!/usr/bin/env python3
"""A private notes folder for an AI player, as a tiny MCP server (stdio, no dependencies).

The player can keep its own notes (clues, names, plans) across turns and sessions, and read
nothing else on this machine, except the read-only folders you allow (e.g. where its AI
client saves long tool results that didn't fit in the conversation).

    python scripts/notes_mcp.py --root ~/tabletop-notes [--seat NAME] [--read-only DIR ...]

Each seat gets its own folder, <root>/<seat>, so players don't read each other's notes. The
seat comes from --seat or the TABLETOP_SEAT environment variable, which the table runner
(scripts/table.py) sets for every AI turn to "<table file name>/<character name>".

Tools: notes_list, notes_read (also reads files in the --read-only folders, by absolute path),
notes_write.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

MAX_READ = 60000


def slug(text):
    return re.sub(r"[^\w.-]+", "-", text.strip(), flags=re.UNICODE).strip("-") or "player"


class Notes:
    def __init__(self, root, seat, read_only):
        self.dir = Path(root).expanduser().joinpath(*[slug(p) for p in seat.split("/") if p])
        self.dir.mkdir(parents=True, exist_ok=True)
        self.read_only = [Path(d).expanduser().resolve() for d in read_only]

    def _mine(self, path):
        p = (self.dir / str(path or "").lstrip("/")).resolve()
        if p != self.dir.resolve() and self.dir.resolve() not in p.parents:
            raise ValueError("Only your notes folder: use a relative path such as clues.md")
        return p

    def _readable(self, path):
        p = Path(str(path)).expanduser()
        if p.is_absolute():
            p = p.resolve()
            if any(p == d or d in p.parents for d in self.read_only) or self.dir.resolve() in p.parents:
                return p
            raise ValueError("That file is outside your notes and the folders you may read.")
        return self._mine(path)

    def list(self, path=""):
        base = self._mine(path)
        if not base.exists():
            return "(empty)"
        files = sorted(str(f.relative_to(self.dir)) + ("/" if f.is_dir() else f"  ({f.stat().st_size} bytes)")
                       for f in base.rglob("*"))
        return "\n".join(files) or "(no notes yet)"

    def read(self, path, offset=1, limit=400):
        p = self._readable(path)
        if not p.is_file():
            raise ValueError(f"No such file: {path}")
        lines = p.read_text(errors="replace").splitlines()
        start = max(1, int(offset or 1))
        chunk = lines[start - 1:start - 1 + int(limit or 400)]
        out = "\n".join(f"{start + i}|{line}" for i, line in enumerate(chunk))[:MAX_READ]
        end = start + len(chunk) - 1
        more = f"\n[lines {start}-{end} of {len(lines)}; read on with offset={end + 1}]" if end < len(lines) else ""
        return out + more

    def write(self, path, content, append=False):
        p = self._mine(path)
        if p == self.dir.resolve():
            raise ValueError("path must be a file name, e.g. clues.md")
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a" if append else "w") as f:
            f.write(content)
        return f"{'Appended to' if append else 'Wrote'} {p.relative_to(self.dir.resolve())}"


TOOLS = [
    {"name": "notes_list", "description": "List your notes (your private folder for this table).",
     "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "description": "Subfolder, optional."}}}},
    {"name": "notes_read",
     "description": "Read one of your notes by relative path (e.g. clues.md), or, by absolute path, a file your client saved for you (a long tool result it told you to read). Lines are numbered; read long files in parts with offset and limit.",
     "inputSchema": {"type": "object", "properties": {
         "path": {"type": "string"}, "offset": {"type": "integer", "description": "First line, from 1."},
         "limit": {"type": "integer", "description": "How many lines (default 400)."}}, "required": ["path"]}},
    {"name": "notes_write",
     "description": "Write one of your notes (clues, names, plans, your character's state), by relative path such as clues.md. Overwrites it, or adds to its end with append.",
     "inputSchema": {"type": "object", "properties": {
         "path": {"type": "string"}, "content": {"type": "string"},
         "append": {"type": "boolean", "description": "Add to the end instead of overwriting."}},
         "required": ["path", "content"]}},
]


def handle(notes, msg):
    method, mid, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if mid is None:
        return None  # notification
    if method == "initialize":
        result = {"protocolVersion": params.get("protocolVersion", "2024-11-05"),
                  "capabilities": {"tools": {}}, "serverInfo": {"name": "tabletop-notes", "version": "1.0"}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        args = params.get("arguments") or {}
        try:
            fn = {"notes_list": notes.list, "notes_read": notes.read, "notes_write": notes.write}[params.get("name")]
            result = {"content": [{"type": "text", "text": fn(**args)}]}
        except Exception as e:  # report to the model, don't crash
            result = {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}
    elif method == "ping":
        result = {}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, help="folder holding every seat's notes")
    ap.add_argument("--seat", default=os.environ.get("TABLETOP_SEAT") or "player")
    ap.add_argument("--read-only", nargs="*", default=[], help="folders the player may also read")
    args = ap.parse_args()
    notes = Notes(args.root, args.seat, args.read_only)
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            reply = handle(notes, json.loads(line))
        except json.JSONDecodeError:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}
        if reply is not None:
            sys.stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
