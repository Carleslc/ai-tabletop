# assets/: your Call of Cthulhu library

Put your own Call of Cthulhu books here: rulebooks, supplements, adventures, handouts, maps, and character sheets (PDF or images). The Keeper skill searches and reads them page by page with `scripts/library.py`; see [`skills/coc-kp/references/library.md`](../skills/coc-kp/references/library.md).

**This folder is not published.** Books are copyrighted, so this repository's `.gitignore` ignores everything here except this README. If you want to version your books, do it in a **private** repository (and remove the `assets/*` rule from its `.gitignore`). Never push them to a public one.

## Layout

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

- One folder per language (`EN/`, `ES/`, …). OCR picks the language from it: Spanish for `ES/`, English otherwise.
- Give each adventure with extra files (handouts, pregens, maps) its own folder.
- Keep descriptive file names. Mark Keeper-only material in the name (e.g. `Keeper_Maps`, `keeper_only`, `spoiler`) so it is never shown to players.
- If you only have a scenario as a page range inside a bigger book, add a small `.txt` note in its folder saying where to find it (book and page).

## After adding or changing books

```bash
pip install pymupdf                               # once
python scripts/library.py extract                 # text of new/changed PDFs -> library/ (local cache)
python scripts/library.py extract --ocr           # also OCR scanned PDFs (brew install tesseract tesseract-lang)
```

Then ask the Keeper to update the catalog in `library.md` (what each book is, edition, contents, handouts, Keeper-only files).

GitHub rejects files over 100 MB (use compressed PDFs or Git LFS in your private repository) and pushes over 2 GB (push in several commits).
