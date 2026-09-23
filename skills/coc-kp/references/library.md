# Library: rulebooks, supplements, and adventures in `assets/`

Read this when you need an exact rule, a monster/spell/tome write-up, a list of playable adventures, a pre-generated investigator, a handout, or when preparing any scenario that lives in `assets/`.

`assets/` holds the table owner's own Call of Cthulhu books (PDFs and images): rulebooks, supplements, adventures, handouts, and character sheets, organized by language. It is not part of this repository: books are copyrighted, so each owner keeps theirs locally or in a private repository (see `assets/README.md`). **When a book is available, look the rule up instead of relying on memory**, and when rules text and this skill disagree, the book wins (unless the user set a house rule).

## How to read the books

Book PDFs are large (hundreds of pages, sometimes 100 MB). Never load a whole PDF. Use `scripts/library.py` (needs PyMuPDF: `pip install pymupdf`; OCR needs Tesseract) from the repo root:

```bash
python scripts/library.py extract                      # once: all PDFs -> library/<same path>.txt (skips up-to-date files)
python scripts/library.py extract --ocr                # also OCR scanned PDFs (slow)
python scripts/library.py search "pushing|forzar" "Keeper_Rulebook"   # regex over extracted text -> file p.<page>: line
python scripts/library.py toc "<pdf>"                  # bookmarks with pages
python scripts/library.py pages "<pdf>" 155-158        # text of those pages
python scripts/library.py render "<pdf>" 157           # whole page as an image (200 dpi), to read or verify it
python scripts/library.py regions "<pdf>" 86           # handouts on a page: numbered list + preview (see Handouts)
python scripts/library.py render "<pdf>" 86 --near "Handout 2"   # one handout, cropped, label hidden, upright
python scripts/library.py info "<pdf>"                 # page count, usable-text coverage
```

- Paths may be given relative to `assets/`. The `library/` folder is a local, git-ignored cache (a table repository may commit it so that AI players can read its books through the worker); if a `.txt` is missing, run `extract` first. A full `extract` also removes the text of PDFs that were renamed or deleted.
- Page numbers are **PDF page indices** (1-based), which can differ by a few pages from the printed page numbers. Search, then read the surrounding pages with `pages`. With plain tools, `rg -n "term" library/` also works; the text files mark pages as `=== page N ===`.
- Search in the book's language: Spanish books need Spanish terms (`Cordura`, `Guardián`, `forzar la tirada`), English books English terms.
- **Scanned PDFs** have no text layer until OCR'd (`extract` lists them). OCR text is searchable but noisy: stray symbols from borders and illustrations, broken words, mixed-up columns, misread numbers. Some native text layers are garbled too (odd symbols, missing accents, overlapping text).

Without a shell, connected only to the worker, you can still read books whose extracted text is committed in the worker's repository: `book_search` with `path` set to a book's `.pdf` path or a folder (`library/EN`) returns `<file> p.<page>: <line>`, and `book_read` with the book's `.pdf` path and `pages` (`"155-158"`) reads those pages. Rendering pages and handouts needs a shell.

### Extracted text is an index, the page is the source

Use `search` and the `.txt` files to *find* things. Before you rely on a passage, check that it is coherent: sentences that read naturally, names consistent, numbers plausible, columns in order. **If it is not, or if anything exact depends on it, read the page itself**: `render <pdf> <page>` with no other options renders the whole page; read the image (use 300 dpi, or `--rect` to zoom into a column or a small table). Chapter openers and some other pages are full-page illustrations with no text: if the render is just a picture, you have the wrong page, usually the text is on the next one. `pages` is not a fix, since it prints the same text layer. This is mandatory when you:

- quote or closely paraphrase text to players (read-aloud boxes, letters, diaries, NPC lines, handout text);
- use numbers or names that matter (stats, SAN losses, dates, addresses, clue names, spell costs);
- follow a solo gamebook: entry numbers, choices, checks, and "go to N" instructions must come from the page image when the text looks off (OCR often drops or garbles entry numbers);
- adjudicate a rule from a page whose text looks broken.

Never present garbled OCR to a player, and never "fix" it by guessing: read the image and transcribe what the book says.

## How `assets/` is organized

```text
assets/
├── Character Sheets/            blank sheets (per era), starter-set pregens
├── EN/                          English books
│   ├── <core rulebooks, quick-start rules, Keeper references>.pdf
│   ├── <supplement>/            bestiaries, grimoires, setting books (+ their PDF packs)
│   └── Adventures/
│       ├── <adventure or collection>.pdf
│       └── <adventure>/         book + handouts, pregens, player/Keeper maps, portraits
└── ES/                          Spanish books (same layout; adventures in Aventuras/)
```

Other languages follow the same pattern (`assets/<LANG>/`). Files whose name says Keeper (`Keeper_Maps`, `Keepers-Diagrams`, `keeper_only`, `spoiler`…) are Keeper-only. See `assets/README.md` for naming tips.

## Language pairing

Prefer the edition in the table's language. When a book exists in several languages, use either for rules lookup (pick the one with the better text layer), but read scenario text and handouts in the table's language when possible, and keep proper names consistent with the version you present. Spanish 7e terms: Guardián (Keeper), Cordura (SAN), Suerte (Luck), Puntos de Vida (HP), Puntos de Magia (MP), Crédito (Credit Rating), Corpulencia (Build), Bonificación al daño (Damage Bonus), Movimiento (MOV), éxito normal/difícil/extremo (Regular/Hard/Extreme), crítico/pifia (critical/fumble), forzar la tirada (push), dado de bonificación/penalización (bonus/penalty die), Mitos de Cthulhu (Cthulhu Mythos), Idea (Idea roll).

## Catalog

The sections below describe *this* library. They start empty: the library owner fills them in, or asks you to. **To build or update the catalog**: list `assets/` (`find assets -type f`), run `extract` (with `--ocr` for scans), and for each book check its bookmarks (`toc`), introduction, and credits page; note the language, rules edition (7e stat blocks use characteristics of 15–90; older editions use 3–18, a Resistance Table, or "POW×5"-style rolls), contents, player count, era, which files are handouts, pregens, or maps, what is Keeper-only, and whether it is scanned. Keep entries short and spoiler-free (contents are scenario titles and premises, never secrets). Until the catalog is filled, explore `assets/` the same way when you need a book.

Legend for the tables: **7e** = ready to play. **old** = earlier edition, convert as you go (see Converting). 🖼 = scanned (OCR'd text, verify against the page image). Paths are relative to `assets/`.

### Core rules

| Book | Path(s) by language | Use for |
|---|---|---|
| *(core Keeper rulebook)* | | The authoritative rules. |
| *(investigator/player handbook)* | | Character creation, occupations, equipment, era reference. |
| *(quick-start / introductory rules)* | | Compact rules; often include a first scenario and ready-made investigators. |
| *(Keeper references, conversion guidelines)* | | Fast lookups, Keeper craft, converting older editions. |

Chapter start pages (PDF pages) in the core Keeper rulebook, per language (fill from `toc`): creating investigators, skills, game system, combat, chases, sanity, magic, playing the game / Keeper advice, tomes, grimoire, artifacts, monsters, scenarios, appendices. Chapter title pages are often followed by a full-page illustration, so the text starts a page or two later.

### Mythos references and supplements

| Book | Path | Use for |
|---|---|---|
| *(bestiary)* | | Monster and deity stat blocks. |
| *(grimoire)* | | Spells: costs, casting time, variants. |
| *(setting or era supplement)* | | Setting detail; may change rules (occupations, skills). |

Keep stat blocks Keeper-only. Describe monsters through the investigators' senses; never read out numbers.

### Character sheets and pre-generated investigators

- Blank sheets per era and language: *(paths)*. Use their field layout when writing cards; the markdown templates in `prep_persistence.md` mirror them.
- Pregens: *(paths, and which scenarios they belong to)*. Offer them when the user wants to start quickly; they are built to fit the scenario's hooks.

### Solo adventures (gamebooks) — use "Solo gamebook mode"

| Adventure | Path(s) by language | Ed. | Notes |
|---|---|---|---|
| | | | |

**Never mix entry numbers between editions or languages**: remakes and translations of the same solo often renumber entries. Always follow the entries of the one book being played. Old-edition solos use pre-7e rules: convert rolls on the fly.

### Group adventures

| Adventure | Path(s) by language | Ed. | Contents (scenarios, players, era, handouts/pregens/maps, Keeper-only files) |
|---|---|---|---|
| | | | |

When the same adventure exists in several editions (e.g. an old translation and a 7e original), note which scenarios match, so you can take rules and stats from the 7e book and names and prose from the table-language one.

## Converting pre-7e material (summary)

Many adventures, especially older translations, use earlier editions. The official 7th Edition conversion guidelines (also an appendix of the 7e Keeper rulebook) are the full reference; apply them on the fly, silently:

- **Characteristics**: multiply old STR, CON, SIZ, DEX, APP, INT, POW, EDU by 5 (EDU above 18: 18→90, 19→91 … 27+→99). The old SAN characteristic is dropped (Sanity points stay). Luck and HP can stay as written; Build is new (from STR+SIZ); keep old MOV for simplicity.
- **Skills**: most transfer unchanged. Merged skills: Fighting (Brawl) replaces Punch/Kick/Head Butt/Grapple; Firearms (Rifle/Shotgun) takes the better of the two. Consider new Charm and Intimidate where Fast Talk/Persuade/Bargain are called for.
- **Characteristic rolls**: ×1 → Extreme; ×2 or ×3 → Hard; ×4 to ×6 → Regular; ×7 or ×8 → Regular with a bonus die. (So "POW×2", "POD x 2" in Spanish, is a Hard POW roll.)
- **Resistance Table** → opposed roll against the ×5 value (STR 16 → STR 80).
- **Modifiers**: ignore ±5 or less; bigger ones become a difficulty change or a bonus/penalty die (≈ ±20%).
- **Idea rolls** in old scenarios were for noticing clues: give obvious clues freely, use the 7e Idea roll only when play stalls. Old failure consequences can become pushed-roll consequences.
- **Monsters**: characteristics ×5; attacks per round from the text; Fighting % = main attack; grabs become fighting maneuvers; characteristic drains ×5 (e.g. 1D3 STR → 1D10+5). HP, armor, damage bonus, and MOV unchanged.
- **Tomes**: old Mythos gain ÷3 (round down) = initial reading (CMI); remainder = full study (CMF). **Poison** POT 1-9 Mild, 10-19 Strong, 20+ Lethal.
- **System-neutral scenarios**: map their generic checks to the closest 7e skill or characteristic.

## Handouts and maps

- Handouts are player-facing only when the adventure says so. Files or pages marked for the Keeper are **never** shown to players. Maps can also carry Keeper-only information (hidden rooms, a secret's location, where someone hides): check a map against the scenario before showing it, and describe the place instead if it gives something away.
- Show a handout **at the moment the investigator obtains it, and only that one**. Pages often hold several handouts given at different times (a sheet of numbered handouts, or handouts printed inside the adventure next to Keeper text), sometimes overlapping, rotated sideways, or full-page.
- Workflow to extract one handout from a PDF page or an image file:
  1. `regions <file> <page>` lists the handouts found on the page (numbered), each with its label ("Ayuda de juego 3", "Handout 9", "Handout: Name 2"), position, detected rotation and a text sample, and saves a preview with numbered boxes and a 10% grid. Look at the preview if the list is not conclusive.
  2. `render <file> <page> --near "Handout 2"` (label text, or any text of the handout itself) or `--region <k>` renders just that handout at 200 dpi: cropped, rotated upright when printed sideways, with the Keeper label and page number removed, and with overlapping handouts and nearby book text hidden.
  3. **Look at the result** before showing it: the desired handout, complete, legible, upright, nothing extra (no Keeper text, no other handout, no label). If not, adjust: `--rect x0,y0,x1,y1` (page fractions read off the preview grid) to fix the area, `--rotate 90|180|270` to rotate, `--pad` to add margin, `300` dpi for small print, `--no-isolate` if hiding removed part of the handout, `--keep-labels` if the "label" was actually in-world text, `--raster` for scanned pages. Iterate until it is right.
- Image-file handouts that hold a single handout can be shown directly. On scanned pages and image files, labels are found by OCR and painted over; on normal PDF pages they are removed from the text layer without touching the picture.
- If a clean image cannot be obtained, give the handout's text instead: transcribe it from the page image, or use plain-text handout versions if the adventure includes them. Never show a crop that includes Keeper text or another handout.
- On the Issue table, publish the rendered handout to the table's repository and link it from your comment (see "Publishing player material" in `SKILL.md`); if you cannot, describe the handout or paste its text. Never publish whole pages of the books.

## Prep with the library

When starting an adventure from `assets/`: `extract` it (OCR if scanned), read the introduction and Keeper background privately, build `00_keeper/scenario_frame.md` as in `prep_persistence.md` pointing at the source PDF and page numbers instead of copying the PDF, list its handouts/pregens, and note if it needs conversion. Keep all of this Keeper-only, in your private campaign folder.
