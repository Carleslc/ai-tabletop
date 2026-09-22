# coc-tabletop

Turn GitHub Issues into a Call of Cthulhu tabletop.

One fork, everyone at the table. The Keeper and the player AIs each connect through their own clients and play together in the same GitHub repo via Issues. Transparent dice rolls, permanent session logs, seamless cross-device continuity.

If you already play in a group chat (Discord, Telegram…) or just want to play in a single AI conversation, you don't need to deploy the worker — feed the `skills/` SKILL.md files directly to your AIs. The worker is for people without a group chat, or who want sessions recorded publicly on GitHub.

Sessions can be played in any language. The skills are written in English; the Keeper narrates in whatever language you speak to it (e.g. Spanish), or the one you ask for.

## What this is

A tabletop infrastructure pack with four components:

1. **Cloudflare Worker** — A zero-dependency MCP server that lets AI clients (claude.ai / ChatGPT / Claude Code) read and write your GitHub repo. Files are the campaign library ("books"), Issues are the table.
2. **Keeper + Player skills** — Behavior guides for AIs. `coc-kp` teaches an AI to be the Keeper running the game. `coc-player` teaches an AI to be an investigator playing at the table.
3. **Helper scripts** — `scripts/roll.py` (dice roller with CoC 7e success levels), `scripts/library.py` (search and read the PDF books page by page), and `scripts/music.py` (scene background music on macOS).
4. **Library** (`assets/`, your own books, not included) — rulebooks, Mythos references, character sheets, and adventures in any language, catalogued for the Keeper in [`skills/coc-kp/references/library.md`](skills/coc-kp/references/library.md).

Together: feed the skills to different AIs (one as Keeper, the rest as players). They use the worker to "sit around the table" in your GitHub repo's Issues. Comments are turns.

## Ways to play

| Mode | Keeper | Investigators | What you need |
|---|---|---|---|
| **Solo gamebook** | The published solo adventure (e.g. a PDF) | You | `coc-kp` in *solo gamebook mode* as an assistant: it tracks your sheet, rolls dice, and follows the numbered entries without spoiling others. Or run the book fully by yourself with `scripts/roll.py`. |
| **Solo with an AI Keeper** | AI (`coc-kp`) | You, optionally plus AI teammates | One AI conversation. Teammates can be run by the Keeper (lightweight) or by separate AIs with `coc-player` (true hidden information). |
| **You play, AI players join** | AI (`coc-kp`) | You + other AIs (`coc-player`) | The worker (or a group chat), one AI client per seat. Use this when a scenario needs more players than you. |
| **You Keep, AIs play** | You | AIs (`coc-player`) | The worker (or a group chat). |
| **Fully simulated** | AI (`coc-kp`) | AIs (`coc-player`) | The worker. You read the Issue thread like a story. Use separate AI sessions per seat so players never see the Keeper's secrets. |

Each role signs its Issue comments with a tag: `[KP]`, `[Character Name]`.

## Quick start without the worker (single conversation)

1. Paste `skills/coc-kp/SKILL.md` into your AI (as a system prompt, project instructions, or a Claude skill — see below).
2. Optionally attach your scenario PDF, or a solo adventure PDF.
3. Say something like *"Let's play Call of Cthulhu in Spanish, I'll be the investigator"* or *"Help me play this solo adventure"*.

### Using the skills in Claude Code

Claude Code loads skills from `.claude/skills/` (per project) or `~/.claude/skills/` (global). From the repo root:

```bash
mkdir -p .claude && ln -s ../skills .claude/skills
```

Then invoke `/coc-kp` or `/coc-player`. Run Claude Code from the repo root so `scripts/roll.py` and `scripts/music.py` resolve.

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
- Deploy command: leave empty (Cloudflare reads `wrangler.toml`)

After deploying, go to Worker → **Settings** → **Variables and Secrets** and add:

| Name | Type | Value |
|---|---|---|
| `AUTH_TOKEN` | Secret | A password you choose |
| `GITHUB_TOKEN` | Secret | The `github_pat_...` from step 2 |
| `GITHUB_REPO` | Text | `yourname/your-repo-name` |
| `DEFAULT_BRANCH` | Text | `main` |

### 4. Connect AI clients

Your worker URL will be something like `https://coc-tabletop.<your-subdomain>.workers.dev`.

In claude.ai → Settings → Connectors → Add custom connector, enter:

```
https://coc-tabletop.<your-subdomain>.workers.dev/mcp?token=<your AUTH_TOKEN>
```

Then give `skills/coc-kp/SKILL.md` to one AI (as Keeper, or invoke `/coc-kp`) and `skills/coc-player/SKILL.md` to each AI player.

The Keeper opens an Issue in your repo as the table using `table_post`. Players take turns by commenting on the Issue with `table_reply`.

## Tools (MCP tools exposed by the worker)

### Bookshelf (repo files: scenarios, character sheets, logs)

| Tool | Purpose |
|---|---|
| `book_search` | Search markdown files |
| `book_read` | Read a file |
| `book_list` | List directory contents |
| `book_write` | Write a file (save sheets, logs, prep notes) |

### Table (GitHub Issues: session threads, turns, OOC)

| Tool | Purpose |
|---|---|
| `table_list` | List table topics |
| `table_read` | Read a topic + all replies |
| `table_post` | Create a new topic (start a session, recruit, OOC) |
| `table_reply` | Reply to a topic (your turn) |
| `table_update` | Edit topic title/body |
| `table_tags` | Manage topic labels |
| `table_close` | Close/reopen a topic |

## Scripts

```bash
python scripts/roll.py check 55   # 1D100 vs 55 → Critical / Extreme / Hard / Regular success, Failure, Fumble
python scripts/roll.py d100
python scripts/roll.py 1d6
python scripts/roll.py 1d4+2
```

```bash
python scripts/music.py play <youtube-url>   # macOS: open ambient track, closing the previous one
python scripts/music.py cut                  # instant silence for a scare
python scripts/music.py resume
python scripts/music.py stop
```

## Library

The Keeper can use your own Call of Cthulhu books: rulebooks, supplements, and adventures (PDFs, handout images). This repository ships no books. Put yours in `assets/`, one folder per language (`assets/EN/`, `assets/ES/`, …); see [`assets/README.md`](assets/README.md) for the layout and [`skills/coc-kp/references/library.md`](skills/coc-kp/references/library.md) for how the Keeper uses them and the catalog it keeps of them. The Keeper never loads whole books: it extracts their text once and then searches and reads single pages.

```bash
pip install pymupdf
python scripts/library.py extract                  # all PDFs -> library/*.txt (git-ignored cache)
python scripts/library.py search "Sanity|Cordura"  # matches with file and page number
python scripts/library.py pages "EN/<book>.pdf" 152-154
python scripts/library.py render "<pdf>" 12        # page -> PNG (200 dpi), e.g. to read a scanned page
python scripts/library.py regions "<pdf>" 12       # list the handouts on a page (+ preview)
python scripts/library.py render "<pdf>" 12 --near "Handout 3"   # just that handout, cropped and upright
```

Scanned PDFs need OCR: `brew install tesseract tesseract-lang`, then `python scripts/library.py extract --ocr`.

The books are copyrighted: keep them out of any public repository (this fork's `.gitignore` ignores `assets/` for that reason; to version your books, use a private repository and drop that rule there), and share with your players only the handouts they would receive at the table.

## Adding features

This repo follows a feature-folder convention; features stay independent of each other:

1. Create `features/<name>/` with `state.json` (initial state), `skill.md` (gameplay rules), and optionally `panel/` (frontend).
2. If the feature needs new MCP tools, register them in `src/index.js`.
3. `git push` — Cloudflare auto-deploys.

The worker only does generic read/write (files + Issues). No game logic lives there.

## Credits

- Keeper skill based on [coc-kp-host](https://github.com/SumanasJ/coc-kp-host) by SumanasJ (MIT)
- Worker pattern inspired by [my-memory](https://github.com/sakisakisa-design/my-memory)

## License

MIT
