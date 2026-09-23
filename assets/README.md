# assets/: your tabletop RPG library

Put your own books here, one folder per game system: rulebooks, supplements, adventures, handouts, maps, and character sheets (PDF or images). Each system's GM skill searches and reads them page by page with `scripts/library.py`, and keeps a catalog of them in its `references/library.md` (for Call of Cthulhu, [`skills/coc-kp/references/library.md`](../skills/coc-kp/references/library.md)).

**This folder is not published.** Books are copyrighted, so this repository's `.gitignore` ignores everything here except this README. If you want to version your books, do it in a **private** repository (and remove the `assets/*` rule from its `.gitignore`). Never push them to a public one.

## Layout

```text
assets/
├── CoC/                             Call of Cthulhu
│   ├── Character Sheets/            blank sheets (per era), starter-set pregens
│   ├── EN/                          English books
│   │   ├── <core rulebooks, quick-start rules, GM references>.pdf
│   │   ├── <supplement>/            bestiaries, grimoires, setting books (+ their PDF packs)
│   │   └── Adventures/
│   │       ├── <adventure or collection>.pdf
│   │       └── <adventure>/         book + handouts, pregens, player/GM maps, portraits
│   └── ES/                          Spanish books (same layout; adventures in Aventuras/)
├── DnD/                             another system, same idea
│   └── EN/
└── 7Sea/
    └── EN/
```

- One folder per system, with a short name (`CoC`, `DnD`, `7Sea`…), and inside it one folder per language (`EN/`, `ES/`, …). OCR picks the language from that folder (`ES/` → Spanish, `FR/` → French…; English otherwise).
- Material shared by every language of a system (such as character sheets) can sit directly in the system folder.
- Give each adventure with extra files (handouts, pregens, maps) its own folder.
- Keep descriptive file names. Mark GM-only material in the name (e.g. `Keeper_Maps`, `GM_only`, `keeper_only`, `spoiler`) so it is never shown to players.
- If you only have a scenario as a page range inside a bigger book, add a small `.txt` note in its folder saying where to find it (book and page).

## After adding or changing books

```bash
pip install pymupdf                               # once
python scripts/library.py extract                 # text of new/changed PDFs -> library/ (local cache)
python scripts/library.py extract --ocr           # also OCR scanned PDFs (brew install tesseract tesseract-lang)
```

Then ask the system's GM to update the catalog in its skill's `references/library.md` (what each book is, edition, contents, handouts, GM-only files).

GitHub rejects files over 100 MB (use compressed PDFs or Git LFS in your private repository) and pushes over 2 GB (push in several commits).
