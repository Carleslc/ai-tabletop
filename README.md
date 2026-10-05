# ai-tabletop

Turn GitHub Issues into a tabletop role-playing table, run and played by AI agents and people.

One set of tools for any game system: the table (GitHub Issues), the worker, the dice and the book library are shared, and each system brings its own skills with its rules. The game master (GM) and the player AIs each connect through their own clients and play together in the same GitHub repo via Issues. Transparent dice rolls, permanent session logs, seamless cross-device continuity.

If you already play in a group chat (Discord, Telegram…) or just want to play in a single AI conversation, you don't need to deploy the worker — feed the skills' SKILL.md files directly to your AIs. The worker is for people without a group chat, or who want sessions recorded on GitHub.

Sessions can be played in any language. The skills are written in English; the GM narrates in whatever language you speak to it (e.g. Spanish), or the one you ask for.

## For AI agents: start here

If a person gave you this repository's link to play a tabletop role-playing game, this is how to get them playing.

1. **Ask what they want**, briefly: which game (see [Systems](#systems)); will you be the GM (you run the game) or play a character; the language; alone or with other players (humans or AIs); and their own scenario (a PDF, a published adventure) or an original one.
2. **Load the skill for that system and your role** (see [Systems](#systems)) and follow it from then on:
   - **GM** (the usual case): the system's GM skill, e.g. [`skills/coc-kp/SKILL.md`](skills/coc-kp/SKILL.md) for Call of Cthulhu, plus the files in its `references/` folder when it tells you to read them.
   - **Player**, when someone else (human or AI) is the GM: the system's player skill, e.g. [`skills/coc-player/SKILL.md`](skills/coc-player/SKILL.md).

   Without a clone, read them raw, e.g. `https://raw.githubusercontent.com/Carleslc/ai-tabletop/main/skills/coc-kp/SKILL.md`.

   If the game has no skills here yet, say so: you can still run it from its rulebook, or the person can add the system (see [Adding a game system](#adding-a-game-system)).
3. **Set up the table** that fits (see [Ways to play](#ways-to-play)):
   - **In this conversation** (one person, plus any AI teammates you run as the GM): nothing to set up. Start with the skill's opening questions. With a shell, clone this repository and roll with `scripts/roll.py`; without one, roll yourself and report each result.
   - **On GitHub** (several players, separate AI players, or a permanent record): the table is an Issue in a table repository, and each comment is a turn. The person does the account steps (create the repository, a token, the worker, invite the players); guide them through [Quick start with the worker](#quick-start-with-the-worker). A GM with a shell and the `gh` CLI can run the table without the worker (`gh issue create`, `gh issue comment`).
   - **With the person's own books**: they are not in this repository. They go in `assets/<System>/<LANG>/` of the person's private copy (see [Library](#library)). With other players, keep the adventures out of the repository the players can read ([step 5](#5-keep-the-adventures-away-from-the-players-multiplayer)): the GM works from the private library, the players from the table repository.
4. **Keep the roles apart.** As a player, never read adventures, GM books or the GM's notes. As the GM, never post hidden information at the table.

## What this is

A tabletop infrastructure pack with four components:

1. **Cloudflare Worker** — A zero-dependency MCP server that lets AI clients (claude.ai / ChatGPT / Claude Code) read and write your GitHub repo. Files are the campaign library ("books"), Issues are the table.
2. **Skills, per game system** — Behavior guides for AIs: a GM skill teaches an AI to run the game, a player skill to play a character at the table. Each system has its own, because each has its own rules (see [Systems](#systems)).
3. **Helper scripts**, shared by every system — `scripts/roll.py` (standard dice notation for any system, plus Call of Cthulhu checks), `scripts/library.py` (search and read the PDF books page by page, extract handouts), and `scripts/music.py` (scene background music on macOS).
4. **Library** (`assets/`, your own books, not included) — rulebooks, supplements, character sheets, and adventures, one folder per system and language, catalogued for the GM in the GM skill's `references/library.md`.

Together: feed the skills to different AIs (one as GM, the rest as players). They use the worker to "sit around the table" in your GitHub repo's Issues. Comments are turns.

## Systems

| System | Books in | GM skill | Player skill | GM tag | Table label |
|---|---|---|---|---|---|
| Call of Cthulhu 7th Edition | `assets/CoC/` | [`coc-kp`](skills/coc-kp/SKILL.md) (the Keeper) | [`coc-player`](skills/coc-player/SKILL.md) (an investigator) | `[KP]` | `Call of Cthulhu` |

Each table Issue carries its game's label, so one table repository can hold games of several systems and list them by label. Skills are named `<system>-<role>`: the player skill is `<system>-player`, and the GM skill takes the system's name for its GM (`coc-kp` for the Keeper; a Dungeons & Dragons one would be `dnd-dm`).

## Ways to play

| Mode | GM | Players | What you need |
|---|---|---|---|
| **Solo gamebook** | The published solo adventure (e.g. a PDF) | You | The GM skill as an assistant (`coc-kp` has a *solo gamebook mode*): it tracks your sheet, rolls dice, and follows the numbered entries without spoiling others. Or run the book fully by yourself with `scripts/roll.py`. |
| **Solo with an AI GM** | AI (GM skill) | You, optionally plus AI teammates | One AI conversation. Teammates can be run by the GM (lightweight) or by separate AIs with the player skill (true hidden information). |
| **You play, AI players join** | AI (GM skill) | You + other AIs (player skill) | The worker (or a group chat), one AI client per seat. Use this when a scenario needs more players than you. |
| **You GM, AIs play** | You | AIs (player skill) | The worker (or a group chat). |
| **Fully simulated** | AI (GM skill) | AIs (player skill) | The worker. You read the Issue thread like a story. Use separate AI sessions per seat so players never see the GM's secrets. |

Each role signs its Issue comments with a tag: the GM with its system's tag (`[KP]` in Call of Cthulhu), players with `[Character Name]`.

On GitHub, the [table runner](#table-runner) passes the turn around for any of these mixes: AI seats run from your machine, people comment on the Issue (or type their turn in its terminal).

## Quick start without the worker (single conversation)

1. Paste your system's GM skill into your AI, e.g. `skills/coc-kp/SKILL.md` (as a system prompt, project instructions, or a Claude skill — see below).
2. Optionally attach your scenario PDF, or a solo adventure PDF.
3. Say something like *"Let's play Call of Cthulhu in Spanish, I'll be the investigator"* or *"Help me play this solo adventure"*.

### Using the skills in Claude Code

Claude Code loads skills from `.claude/skills/` (per project) or `~/.claude/skills/` (global). From the repo root:

```bash
mkdir -p .claude && ln -s ../skills .claude/skills
```

Then invoke a skill by name, e.g. `/coc-kp` or `/coc-player`. Run Claude Code from the repo root so `scripts/roll.py` and `scripts/music.py` resolve.

## Quick start with the worker

### 1. Fork this repo

Click Fork in the top right. Set it to Private if you want only invited people to see the table.

### 2. Generate a GitHub token

GitHub → Settings → Developer settings → **Fine-grained tokens** → Generate new token:

- Repository access: **Only select repositories** → your forked repo
- Permissions:
  - **Contents** → Read and write
  - **Issues** → Read and write
- Copy the `github_pat_...` token

### 3. Deploy to Cloudflare

CF Dashboard → **Workers & Pages** → **Create** → **Workers** →
**Connect to Git** → select your fork:

- **Root directory**: leave empty (repo root)
- Build command: leave empty (zero dependencies)
- Deploy command: leave empty (Cloudflare reads `wrangler.toml`), or `npx wrangler deploy --name <worker-name>` to choose the worker's name, which is what its URL uses

Leave **Enable preview builds** unchecked and **API token** on *Create new token* (that token only lets Cloudflare deploy the worker; it is not `AUTH_TOKEN`). Do not add the variables below under *Build variables*: those only exist while building.

After deploying, go to Worker → **Settings** → **Variables and Secrets** and add:

| Name | Type | Value |
|---|---|---|
| `AUTH_TOKEN` | Secret | A password you choose |
| `GITHUB_TOKEN` | Secret | The `github_pat_...` from step 2 |
| `GITHUB_REPO` | Text | `yourname/your-repo-name` |
| `DEFAULT_BRANCH` | Text | `main` |

### 4. Connect AI clients

Your worker URL is `https://<worker-name>.<your-subdomain>.workers.dev` (the name from `wrangler.toml`, or the one you passed to `--name`).

In claude.ai → Settings → Connectors → Add custom connector, enter:

```
https://<worker-name>.<your-subdomain>.workers.dev/mcp?token=<your AUTH_TOKEN>
```

Then give the GM skill to one AI (e.g. `skills/coc-kp/SKILL.md`, or invoke `/coc-kp`) and the player skill to each AI player (e.g. `skills/coc-player/SKILL.md`).

The GM opens an Issue in your repo as the table using `table_post`, labeled with the game (e.g. `Call of Cthulhu`). Players take turns by commenting on the Issue with `table_reply`.

### 5. Keep the adventures away from the players (multiplayer)

Anyone invited to a repository can read all of it, so a single repository holding both the table and your adventures lets any player — human or AI — read ahead. Split them:

- **A table repository**, shared with your players: the session Issues, player-facing books (player handbooks, introductory rules, character sheets), and what the GM hands out: character sheets, handout images to link from a comment, session recaps. No adventures, no GM books, no GM notes.
- **Your library**, private and unshared: adventures, GM books, handouts, prep, and the GM's notes on the adventure or campaign. The GM reads the books locally with `scripts/library.py`; they never need to be online.

The GM is an AI agent that can run commands where your library is (Claude Code, Codex, Gemini CLI… on your computer) and needs no worker: it runs the table with the `gh` CLI and publishes player material by pushing to a clone of the table repository, both with your own GitHub credentials. Its private notes on the adventure or campaign stay local or in your library repository.

The worker is for the AI players without a shell (claude.ai, ChatGPT…). Deploy it from the table repository, so the worker takes that repository's name:

1. Copy `src/index.js` and `wrangler.toml` from this repository to the table repository. In its `wrangler.toml`, set `name` to the table repository's name and add its variables:

   ```toml
   [vars]
   GITHUB_REPO = "<you>/<table-repo>"
   DEFAULT_BRANCH = "main"
   ```
2. Connect the table repository in Cloudflare as in [step 3](#3-deploy-to-cloudflare), with the default deploy command. In **Settings** → **Build** → **Build watch paths**, set the include paths to `src/*` and `wrangler.toml` (instead of `*`), so that pushing books or player material doesn't redeploy the worker.
3. Add the secrets: `GITHUB_TOKEN`, a token for the table repository with **Issues: read and write** and **Contents: read-only**; and `AUTH_TOKEN`, shared with the AI players' clients.

When `src/index.js` changes here, copy it to the table repository by hand.

With a read-only Contents scope, a player AI can read the thread and the table's books and post its turns, but cannot write files. Human players need no worker at all: they comment on the Issue from the GitHub website.

The worker cannot read PDFs, so let it read the table's books through their extracted text: in the table repository, change `library/` to `library/renders/` in `.gitignore`, run `python scripts/library.py extract` (add `--ocr` for scanned books), and commit `library/`. The AI players then search a book with `book_search` and a `path`, and read it by pages with `book_read`. On the Workers free plan (10 ms of CPU per request), search one book at a time rather than a folder of big books.

Which skill each agent uses:

- **GM**: the system's GM skill (e.g. `skills/coc-kp/`) from your library repository, where you can add your book catalog and campaign notes. Start the agent there, since it reads the books locally.
- **AI players**: a copy of the system's player skill (e.g. `skills/coc-player/`) in the table repository, adapted to it (everything there is player-safe; say where the extracted text and the GM's material live). A player agent should have access to the table repository only, never to your library. The table repository is not a fork, so copy changes to the player skills there by hand.
- The skills in this repository are the generic versions: the base for improvements, not for play.

## Tools (MCP tools exposed by the worker)

### Bookshelf (repo files: scenarios, character sheets, logs)

| Tool | Purpose |
|---|---|
| `book_search` | Search markdown files; with a `path`, the extracted text of a book or folder (returns page numbers) |
| `book_read` | Read a file; a book's `.pdf` path reads its extracted text, optionally only some `pages`; an image (handout, map) comes back as an image |
| `book_list` | List directory contents |
| `book_write` | Write a text file (sheets, recaps); needs a token with Contents write |

### Table (GitHub Issues: session threads, turns, OOC)

| Tool | Purpose |
|---|---|
| `table_list` | List table topics |
| `table_read` | Read a topic and its replies (`last` / `from` for only the latest ones) |
| `table_post` | Create a new topic (start a session, recruit, OOC) |
| `table_reply` | Reply to a topic (your turn) |
| `table_update` | Edit topic title/body |
| `table_tags` | Manage topic labels |
| `table_close` | Close/reopen a topic |

## Scripts

```bash
python scripts/roll.py 1d6
python scripts/roll.py 1d8+2d6+3       # several terms
python scripts/roll.py 2d20kh1+5       # keep highest (advantage); kl = keep lowest
python scripts/roll.py 4d6dl1          # drop lowest (dh = drop highest)
python scripts/roll.py 3d6!            # exploding dice
python scripts/roll.py "5d10>=8"       # dice pool: count successes (also 5d10!>=8)
python scripts/roll.py 4dF             # Fate dice
python scripts/roll.py check 55        # Call of Cthulhu: d100 vs 55 → Critical / Extreme / Hard / Regular success, Failure, Fumble
python scripts/roll.py check 55 --bonus 1   # with a bonus die (or --penalty N)
```

```bash
python scripts/music.py play <youtube-url>   # macOS: open ambient track, closing the previous one
python scripts/music.py cut                  # instant silence for a scare
python scripts/music.py resume
python scripts/music.py stop
```

## Table runner

`scripts/table.py` plays a session on a GitHub Issue turn by turn, with any mix of AI agents and people in the GM's and players' seats. It needs Python 3 and the [`gh` CLI](https://cli.github.com/) signed in with access to the table repository; Pillow is optional (to send an AI player several new images at once).

```bash
python scripts/table.py run tables/my-table.json            # plays until the GM ends the session
python scripts/table.py run tables/my-table.json --step     # asks before each AI turn: read the Issue, press Enter
python scripts/table.py run tables/my-table.json --turns 5  # stops after 5 AI turns
python scripts/table.py run tables/my-table.json --dry-run  # shows the next AI turn's command and prompt
python scripts/table.py status tables/my-table.json         # whose turn it is, and each seat's session
```

Stop it at any moment (Ctrl+C, or `q` in `--step`) and run it again: it works out whose turn it is from the Issue itself, and keeps each AI seat's conversation in `<table>.state.json` next to the table file.

### Turns

Every comment starts with its author's tag: the GM's (`[KP]` in Call of Cthulhu) or the character's name (`[Henry Ashworth]`). The GM ends each comment with a hidden turn marker, which the GM skills already write:

| Marker | Who acts next |
|---|---|
| `<!-- turn: Name A, Name B -->` | Those characters, in that order |
| `<!-- turn: all -->` (or no marker) | Every player, in seat order |
| `<!-- end -->` | Nobody: the session is over |

Spanish works too: `<!-- turno: … -->`, `<!-- turno: todos -->`, `<!-- fin -->`. When everyone called on has answered, it is the GM's turn again.

Each AI turn gets, in its message, the replies that are new since its last turn (on its first turn, the Issue body and the latest replies), and the images shown in them (handouts, maps) as image input. So an AI seat doesn't need to read the thread itself, nor see a long thread whole.

### The table file

A JSON file per table (examples in [`tables/examples/`](tables/examples/)):

```json
{
  "repo": "yourname/your-table",
  "issue": 1,
  "gm_tag": "KP",
  "seats": [
    { "role": "gm", "name": "KP", "runner": "hermes", "profile": "tabletop-gm", "model": "claude-sonnet-5-5",
      "skills": "coc-kp", "toolsets": "terminal,file,skills,vision", "workdir": "~/ai-tabletop-keeper" },
    { "role": "player", "name": "Henry Ashworth", "runner": "claude", "model": "sonnet",
      "sheet": "table/my-scenario/sheets/henry-ashworth.md" },
    { "role": "player", "name": "Ana Rius", "runner": "human" }
  ],
  "instructions": { "gm": "Nobody answers you during the game: decide, don't ask.", "player": "" }
}
```

| Field | Meaning |
|---|---|
| `repo`, `issue` | The table: repository and Issue number. The GM opens the Issue (its skill says how); then put its number here. |
| `gm_tag` | The GM's tag, without brackets (`KP` in Call of Cthulhu). |
| `seats[].role` | `gm` (one) or `player`. |
| `seats[].name` | The tag of the seat's comments: the GM's tag, or the character's name exactly as in its tag. |
| `seats[].runner` | Who plays the seat: `hermes`, `claude`, `command` or `human` (below). |
| `seats[].posts` | `cli` (default for players): the agent answers with its comment and the runner posts it. `agent` (default for the GM): the agent posts on the Issue itself (with `gh`, or the worker's `table_reply`), as the GM does to publish handouts with its turn. |
| `seats[].sheet` | The character sheet's path in the table repository, for the player's first turn. |
| `seats[].workdir` | Where the agent runs: for the GM, a clone of its private library (it reads the books and rolls with `scripts/roll.py`). |
| `seats[].instructions`, `instructions.gm`, `instructions.player` | Extra instructions added to every turn of that seat or role (style, language, house rules). |
| `seats[].images` | `false` to not send that seat the new images. |
| `seats[].timeout` | Seconds an AI turn may take (default 1800). |
| `prompts` | Override the turn messages (`gm_intro`, `gm_turn`, `player_intro`, `player_turn`; see `DEFAULT_PROMPTS` in the script). |
| `context_chars`, `intro_replies`, `poll_seconds` | How much new text a turn carries (default 40000 characters), how many replies a player's first turn shows (12), how often to check GitHub for a person's comment (30 s). |

The runners:

- **`hermes`**: [Hermes Agent](https://github.com/NousResearch/hermes-agent). Fields: `profile`, `provider`, `model`, `reasoning`, `toolsets`, `skills` (preloaded on the seat's first turn), `max_turns`. One profile per role keeps the GM's and players' tools, skills and memory apart: e.g. a GM profile with a shell in the private library, and a player profile with only the worker as its tools (an MCP server in its `config.yaml`). Each seat is its own Hermes session, resumed every turn.
- **`claude`**: [Claude Code](https://docs.anthropic.com/en/docs/claude-code) in print mode (`claude -p`), resumed every turn. Fields: `model`, and `args` for anything else (`--append-system-prompt-file skills/coc-player/SKILL.md`, `--allowedTools …`, `--mcp-config …`).
- **`command`**: any command line that reads the turn's message on standard input and prints its answer (Codex `exec`, Gemini CLI, your own script). Field: `command` (a list). It gets no session: give it what it needs to remember (e.g. its own conversation file).
- **`human`**: a person. With `"input": "github"` (default) they comment on the Issue from the website, and the runner waits for it. With `"input": "terminal"` they play right here: the runner prints what is new and posts what they type.

### Ways to play with the runner

| Mode | GM seat | Player seats | Example |
|---|---|---|---|
| Fully simulated | AI | AIs | [`fully-simulated.json`](tables/examples/fully-simulated.json). Add `--step` to read along at your pace. |
| You play with an AI GM, optionally with AI players | AI | You (`"input": "terminal"` or on GitHub), plus AIs | [`solo-with-ai-gm.json`](tables/examples/solo-with-ai-gm.json) (also for narrated solo gamebooks) |
| People with an AI GM, optionally with AI players | AI | People (`human`) and AIs | [`ai-gm-with-people.json`](tables/examples/ai-gm-with-people.json) |
| A person GMs, AIs play | You (`human`) | AIs, optionally with people | [`people-gm-ai-players.json`](tables/examples/people-gm-ai-players.json) |

People need only access to the table repository (invite them as collaborators) and comment from the website, starting with their tag. While the runner waits for someone, leave it running (or stop it and run it again later).

Keep each AI seat's access to what its role may know: the players' agents work from the table repository (a clone, or the worker), never from the GM's private library (see [step 5](#5-keep-the-adventures-away-from-the-players-multiplayer)).

## Library

The GM can use your own books: rulebooks, supplements, and adventures (PDFs, handout images). This repository ships no books. Put yours in `assets/`, one folder per system and, inside it, one per language (`assets/CoC/EN/`, `assets/CoC/ES/`, `assets/DnD/EN/`…); see [`assets/README.md`](assets/README.md) for the layout. Each GM skill explains how it uses them and keeps a catalog of them in its `references/library.md` (e.g. [`coc-kp`'s](skills/coc-kp/references/library.md)). The GM never loads whole books: it extracts their text once and then searches and reads single pages.

```bash
pip install pymupdf
python scripts/library.py extract                  # all PDFs -> library/<same path>.txt (git-ignored cache)
python scripts/library.py search "Sanity|Cordura" "CoC/"   # matches with file and page number
python scripts/library.py pages "CoC/EN/<book>.pdf" 152-154
python scripts/library.py render "<pdf>" 12        # page -> PNG (200 dpi), e.g. to read a scanned page
python scripts/library.py regions "<pdf>" 12       # list the handouts on a page (+ preview)
python scripts/library.py render "<pdf>" 12 --near "Handout 3"   # just that handout, cropped and upright
```

Scanned PDFs need OCR: `brew install tesseract tesseract-lang`, then `python scripts/library.py extract --ocr`. The OCR language comes from the language folder (`ES/` → Spanish, `FR/` → French…; English otherwise).

The books are copyrighted: keep them out of any public repository (this fork's `.gitignore` ignores `assets/` for that reason; to version your books, use a private repository and drop that rule there), and share with your players only the handouts they would receive at the table.

## Adding a game system

1. **Books**: put them in `assets/<System>/<LANG>/` (a short folder name: `DnD`, `7Sea`…).
2. **Skills**: create `skills/<system>-<gm>/SKILL.md` (e.g. `dnd-dm`) and `skills/<system>-player/SKILL.md`, with that system's rules, tone, character sheets and GM tag. The Call of Cthulhu skills are a good model: most of `coc-kp` (running the table on Issues, prep and campaign notes, reading the books, publishing player material) is not specific to Call of Cthulhu, only its rules and tone are.
3. **Catalog**: in the GM skill's `references/library.md`, list the system's books in `assets/<System>/` (see `coc-kp`'s for the format).
4. **Dice**: `scripts/roll.py` understands standard dice notation: several terms, keep or drop dice (`2d20kh1`, `4d6dl1`), exploding dice (`d6!`), success pools (`5d10>=8`) and Fate dice (`4dF`); `check` is Call of Cthulhu's d100 roll with bonus and penalty dice. For a mechanic of its own (such as 7th Sea's raises), add a subcommand.
5. Choose the label its tables will carry (the game's name, e.g. `Dungeons & Dragons`) and have the GM skill apply it.
6. Add the system to the [Systems](#systems) table.

## Adding tools

The worker only does generic read/write (files + Issues); no game logic lives there, it belongs in the skills. To add an MCP tool, register it in `src/index.js` and `git push`: Cloudflare redeploys on its own.

## Credits

- Forked from [coc-tabletop](https://github.com/wusaki0723/coc-tabletop) by wusaki0723
- Keeper skill based on [coc-kp-host](https://github.com/SumanasJ/coc-kp-host) by SumanasJ (MIT)
- Worker pattern inspired by [my-memory](https://github.com/sakisakisa-design/my-memory)

## License

MIT
