#!/usr/bin/env python3
"""Searchable text library for the PDFs in assets/ (requires PyMuPDF: pip install pymupdf).

Big rulebooks and adventure PDFs are too heavy to read whole. Extract them once to plain
text with page markers, then search and read only the pages you need.

Usage:
  library.py extract [--ocr] [path ...]
                                       Extract PDFs (default: all of assets/) to library/<path>.txt.
                                       Skips files already up to date (same PDF size; file times are
                                       ignored, since git rewrites them), updating their path if the
                                       PDF moved. Never replaces OCR'd text without --ocr. Prints PDFs with no text
                                       layer (scanned). With --ocr, pages without text are OCR'd with
                                       Tesseract (slow), in the language of the file's language folder
                                       (assets/<System>/ES/ -> Spanish; see OCR_LANGS), English
                                       otherwise. Needs the language data: brew install tesseract-lang.
                                       A full run (no paths) also deletes text of PDFs no longer in assets/.
  library.py search <regex> [subpath]  Case-insensitive search over extracted text.
                                       Prints <file> p.<page>: <line>. subpath filters files,
                                       e.g. "CoC/", "CoC/ES/", "Keeper", or "Adventures/<name>".
  library.py toc <pdf>                 Print the PDF's bookmarks (outline) with page numbers.
  library.py pages <pdf> <n>[-<m>]     Print the text of page n (or pages n..m), 1-based.
  library.py regions <pdf|image> <n> [--raster]
                                       Find the handouts on page n and list them numbered, with their
                                       label ("Ayuda de juego: Nombre 2", "Handout 3"), position as page
                                       fractions, detected rotation and a text sample. Saves a preview with
                                       numbered boxes and a 10% grid (for --rect) to library/renders/.
                                       Works on image files and scanned pages too (--raster forces it;
                                       labels are then found by OCR).
  library.py render <pdf|image> <n> [dpi] [options]
                                       Render page n to library/renders/*.png, 200 dpi by default (300 for
                                       small print). Without options: the whole page, e.g. to read or verify
                                       its text. Options to extract one handout (or part of the page):
                                         --near "<text>"  the handout whose label (or own text) contains it
                                         --region <k>     the k-th handout listed by `regions`
                                         --crop           all handouts on the page, margins dropped
                                         --rect x0,y0,x1,y1  manual area, as page fractions (0-1) or points;
                                                          alone, or to override the area of --near/--region
                                         --rotate <deg>   rotate the output (90, 180, 270); --near/--region
                                                          already rotate sideways handouts upright
                                         --pad <pt>       margin around the handout (default 4)
                                         --keep-labels    keep "Ayuda de juego…"/"Handout…" labels (hidden
                                                          by default) and page numbers
                                         --no-isolate     keep overlapping handouts and nearby book text
                                                          (by default they are hidden from the crop)
                                         --raster         treat the page as an image (scans, image files)
                                       Always look at the result before showing it to a player.
  library.py images <pdf> <n>          Save the large images embedded in page n at original resolution.
                                       Rarely needed: composed handouts are split into layers and tiles,
                                       so prefer `render --near/--region`.
  library.py info <pdf>                Page count, text-layer coverage, and extracted text path.

Extracted text format: each page starts with a line "=== page N ===" (N = PDF page index,
1-based, which can differ from the printed page number). Paths are relative to the repo root.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
LIBRARY = os.path.join(ROOT, "library")
PAGE_RE = re.compile(r"^=== page (\d+) ===$")
READABLE_RE = re.compile(r"[\w\s.,;:!?¡¿'\"()«»\-–—%/]")
WORD_RE = re.compile(r"[^\W\d_]{3,}")


def page_ok(text):
    """True if the page has a usable text layer (not empty, not garbled glyphs)."""
    t = text.strip()
    if len(t) < 80:
        return False
    readable = len(READABLE_RE.findall(t)) / len(t)
    words = WORD_RE.findall(t)
    latin = sum(1 for w in words if all(c < "\u0250" for c in w))
    return readable > 0.9 and len(words) >= 10 and latin / len(words) > 0.9


def fitz():
    try:
        import fitz as f  # PyMuPDF
        # Many book PDFs contain malformed objects that MuPDF skips while printing "syntax error"
        # lines to the console; they are harmless. Real failures still raise exceptions.
        f.TOOLS.mupdf_display_errors(False)
        f.TOOLS.mupdf_display_warnings(False)
        return f
    except ImportError:
        sys.exit("PyMuPDF is required: pip install pymupdf")


def resolve(path):
    """Accept a path relative to cwd, repo root, or assets/."""
    for base in ("", ROOT, ASSETS):
        p = os.path.join(base, path) if base else path
        if os.path.exists(p):
            return os.path.abspath(p)
    sys.exit("not found: %s" % path)


def text_path(pdf):
    rel = os.path.relpath(pdf, ASSETS)
    if rel.startswith(".."):
        rel = os.path.basename(pdf)
    return os.path.join(LIBRARY, os.path.splitext(rel)[0] + ".txt")


def iter_pdfs(paths):
    targets = [resolve(p) for p in paths] if paths else [ASSETS]
    for t in targets:
        if os.path.isfile(t):
            if t.lower().endswith(".pdf"):
                yield t
            continue
        for dirpath, _, files in os.walk(t):
            for name in sorted(files):
                if name.lower().endswith(".pdf"):
                    yield os.path.join(dirpath, name)


# Tesseract language for each language folder (assets/<System>/<LANG>/...).
OCR_LANGS = {"EN": "eng", "ES": "spa", "CA": "cat", "FR": "fra", "DE": "deu", "IT": "ita", "PT": "por"}


def ocr_lang(pdf):
    rel = os.path.relpath(pdf, ASSETS).replace(os.sep, "/")
    for part in rel.split("/")[:-1]:
        if part.upper() in OCR_LANGS:
            return OCR_LANGS[part.upper()]
    return "eng"


def read_header(out):
    """The header of an extracted text (source, size, pages, ocr) as a dict, or None."""
    head = {}
    try:
        with open(out, encoding="utf-8") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line or PAGE_RE.match(line):
                    break
                key, _, value = line.partition(": ")
                head[key] = value
    except OSError:
        return None
    return head


def same_pdf(head, pdf, f):
    """Whether an extracted text still matches its PDF. File times are not used: git
    checkouts and syncing rewrite them. Texts from before the size line compare pages."""
    if "size" in head:
        return head["size"] == str(os.path.getsize(pdf))
    try:
        doc = f.open(pdf)
    except Exception:
        return False
    return head.get("pages") == str(doc.page_count)


def update_header(out, rel, size):
    """Point an up-to-date text at its PDF's current path, and record the PDF size.
    Other header lines (pages, ocr, notes) and the text itself are kept as they are."""
    with open(out, encoding="utf-8", newline="") as fh:
        text = fh.read()
    end = text.index("\n\n") + 1 if "\n\n" in text else len(text)
    lines = ["source: %s" % rel, "size: %d" % size]
    lines += [l for l in text[:end].splitlines() if not l.startswith(("source: ", "size: "))]
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write("\n".join(lines) + "\n" + text[end:])


def extract(paths):
    f = fitz()
    ocr = "--ocr" in paths
    paths = [p for p in paths if p != "--ocr"]
    scanned = []
    for pdf in iter_pdfs(paths):
        out = text_path(pdf)
        rel = os.path.relpath(pdf, ROOT)
        size = os.path.getsize(pdf)
        head = read_header(out)
        if head is not None and same_pdf(head, pdf, f):
            if not ocr or "ocr" in head or text_coverage(out) >= 0.5:
                if head.get("source") != rel or head.get("size") != str(size):
                    update_header(out, rel, size)
                continue
        elif head is not None and "ocr" in head and not ocr:
            # Never replace OCR'd text with an extraction without OCR.
            print("changed, kept its OCR'd text (run `extract --ocr` to redo it): %s" % rel)
            continue
        try:
            doc = f.open(pdf)
        except Exception as e:
            print("ERROR %s: %s" % (rel, e))
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        empty = 0
        lang = ocr_lang(pdf)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("source: %s\nsize: %d\npages: %d\n" % (rel, size, doc.page_count))
            if ocr:
                fh.write("ocr: tesseract (%s), expect recognition errors\n" % lang)
            toc = doc.get_toc()
            if toc:
                fh.write("\n# Bookmarks\n")
                for level, title, page in toc:
                    fh.write("%s- %s (p. %d)\n" % ("  " * (level - 1), title.strip(), page))
            for i, page in enumerate(doc, 1):
                text = page.get_text("text")
                if ocr and not page_ok(text):
                    try:
                        tp = page.get_textpage_ocr(language=lang, dpi=250, full=True)
                        text = page.get_text("text", textpage=tp)
                    except Exception as e:
                        sys.exit("OCR failed (%s). Is tesseract installed with '%s' data?" % (e, lang))
                if not page_ok(text):
                    empty += 1
                fh.write("\n=== page %d ===\n%s" % (i, text))
        coverage = 1 - empty / max(doc.page_count, 1)
        print("%3d%% usable text  %4d pages  %s" % (coverage * 100, doc.page_count, rel))
        if coverage < 0.5:
            scanned.append(rel)
    if not paths:
        prune()
    if scanned:
        print("\nLittle or no text layer (scanned); run `extract --ocr`, or `render` pages to read them:")
        for s in scanned:
            print("  " + s)


def prune():
    """Delete extracted text whose source PDF no longer exists (renamed or removed)."""
    wanted = {text_path(p) for p in iter_pdfs([])}
    for dirpath, _, files in os.walk(LIBRARY):
        if os.path.relpath(dirpath, LIBRARY).split(os.sep)[0] == "renders":
            continue
        for name in files:
            path = os.path.join(dirpath, name)
            if name.endswith(".txt") and path not in wanted:
                os.remove(path)
                print("removed stale %s" % os.path.relpath(path, ROOT))


def text_coverage(out):
    total = filled = 0
    buf = []
    with open(out, encoding="utf-8") as fh:
        for line in fh:
            if PAGE_RE.match(line.rstrip("\n")):
                if total:
                    filled += page_ok("".join(buf))
                total += 1
                buf = []
            elif total:
                buf.append(line)
    if total:
        filled += page_ok("".join(buf))
    return filled / total if total else 0


def search(pattern, subpath=None):
    rx = re.compile(pattern, re.IGNORECASE)
    if not os.path.isdir(LIBRARY):
        sys.exit("library/ is empty: run `library.py extract` first")
    hits = 0
    for dirpath, _, files in os.walk(LIBRARY):
        for name in sorted(files):
            if not name.endswith(".txt"):
                continue
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, LIBRARY)
            if subpath and subpath.lower() not in rel.lower():
                continue
            page = 0
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    m = PAGE_RE.match(line.rstrip("\n"))
                    if m:
                        page = int(m.group(1))
                        continue
                    if rx.search(line):
                        where = "p.%d" % page if page else "header"
                        print("%s %s: %s" % (rel, where, line.strip()[:200]))
                        hits += 1
                        if hits >= 200:
                            print("... (200 hits, refine the pattern or subpath)")
                            return


def toc(pdf):
    doc = fitz().open(resolve(pdf))
    items = doc.get_toc()
    if not items:
        print("(no bookmarks; %d pages)" % doc.page_count)
    for level, title, page in items:
        print("%s- %s (p. %d)" % ("  " * (level - 1), title.strip(), page))


def pages(pdf, spec):
    doc = fitz().open(resolve(pdf))
    a, _, b = spec.partition("-")
    a = int(a)
    b = int(b) if b else a
    for n in range(max(a, 1), min(b, doc.page_count) + 1):
        print("=== page %d ===" % n)
        print(doc[n - 1].get_text("text"))


# ---------- Handouts: regions and rendering ----------

# Short lines that name a handout ("Ayuda de juego: Nombre 2", "AYUDA DE JUEGO 3", "Handout 9",
# "Handout: Name 2 (part 2)"). Headers like "AYUDAS DE JUEGO" (nothing after) do not match.
LABEL_RE = re.compile(
    r"^\s*(ayudas? de juego|ayuda|handout|player aid|player handout)\b\s*[:#.\-]?\s*\S.{0,40}$", re.I)
_DECOR = {}


def page_image(path):
    """Open a PDF or image as a single in-memory PDF document (so it can be edited and drawn on)."""
    f = fitz()
    doc = f.open(path)
    if not doc.is_pdf:
        doc = f.open("pdf", doc.convert_to_pdf())
    return doc


def get_page(path, n):
    doc = page_image(path)
    n = int(n)
    if not 1 <= n <= doc.page_count:
        sys.exit("page out of range (1..%d)" % doc.page_count)
    return doc, doc[n - 1]


def decor_xrefs(path, doc):
    """Images repeated on 3+ pages are page decoration (backgrounds, frames, headers), not handouts."""
    if path not in _DECOR:
        count, dims, edge = {}, {}, {}
        for p in doc:
            for img in {img[:4] for img in p.get_images(full=True)}:
                xref, size = img[0], (img[2], img[3])
                count[xref] = count.get(xref, 0) + 1
                spills = any(max(p.rect.x0 - r.x0, p.rect.y0 - r.y0, r.x1 - p.rect.x1, r.y1 - p.rect.y1) > 8
                             for r in p.get_image_rects(xref))
                if spills:  # frame strips and bleed backgrounds, often a new copy on every page
                    dims[size] = dims.get(size, 0) + 1
                    edge.setdefault(size, set()).add(xref)
        decor = {x for x, c in count.items() if c >= 3}
        for size, c in dims.items():
            if c >= 3:
                decor |= edge[size]
        _DECOR[path] = decor if doc.page_count >= 3 else set()
    return _DECOR[path]


def rdist(a, b):
    dx = max(b.x0 - a.x1, a.x0 - b.x1, 0)
    dy = max(b.y0 - a.y1, a.y0 - b.y1, 0)
    return (dx * dx + dy * dy) ** 0.5


def dir_rotation(d):
    """Degrees to rotate the output so text written in direction d reads left to right."""
    dx, dy = d
    if abs(dx) >= abs(dy):
        return 0 if dx > 0 else 180
    return 270 if dy > 0 else 90


def text_lines(page, textpage=None):
    out = []
    for block in page.get_text("dict", textpage=textpage)["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            if text:
                out.append({"text": text, "rect": fitz().Rect(line["bbox"]), "dir": tuple(line["dir"])})
    return out


def vector_regions(path, doc, page):
    """Candidate handouts on a PDF page: embedded images (not decoration) and large filled boxes."""
    f = fitz()
    area = page.rect.width * page.rect.height
    decor = decor_xrefs(path, doc)
    cands = []
    for img in page.get_images(full=True):
        if img[0] in decor or img[2] < 60 or img[3] < 60:
            continue
        for r in page.get_image_rects(img[0]):
            clipped = r & page.rect
            if clipped.is_empty or clipped.width < 40 or clipped.height < 40:
                continue
            if r.width * r.height > 1.6 * area:  # spills far beyond the page: a spread background
                continue
            cands.append({"rect": clipped, "xrefs": {img[0]}})
    for d in page.get_drawings():
        r = d["rect"] & page.rect
        edges = sum((r.x0 < 3, r.y0 < 3, r.x1 > page.rect.x1 - 3, r.y1 > page.rect.y1 - 3))
        if d.get("fill") is not None and 0.02 * area < r.width * r.height < 0.85 * area and edges < 2:
            cands.append({"rect": r, "xrefs": set()})  # filled box (edge-hugging shapes are page frames)
    # merge near-duplicates (drop shadows, image + its mask) but keep partial overlaps apart
    regions = []
    for c in sorted(cands, key=lambda c: -c["rect"].width * c["rect"].height):
        for r in regions:
            inter = r["rect"] & c["rect"]
            small = min(r["rect"].width * r["rect"].height, c["rect"].width * c["rect"].height)
            if not inter.is_empty and inter.width * inter.height >= 0.85 * small:
                r["rect"] |= c["rect"]
                r["xrefs"] |= c["xrefs"]
                break
        else:
            regions.append({"rect": f.Rect(c["rect"]), "xrefs": set(c["xrefs"])})
    # join tiles: one picture split into images that meet edge to edge
    merged = True
    while merged:
        merged = False
        for i, a in enumerate(regions):
            for b in regions[i + 1:]:
                ra, rb = a["rect"], b["rect"]
                inter = ra & rb
                small = min(ra.width * ra.height, rb.width * rb.height)
                if rdist(ra, rb) > 2 or (not inter.is_empty and inter.width * inter.height > 0.02 * small):
                    continue
                side_by_side = abs(ra.y0 - rb.y0) < 3 and abs(ra.y1 - rb.y1) < 3
                stacked = abs(ra.x0 - rb.x0) < 3 and abs(ra.x1 - rb.x1) < 3
                if side_by_side or stacked:
                    a["rect"] |= rb
                    a["xrefs"] |= b["xrefs"]
                    regions.remove(b)
                    merged = True
                    break
            if merged:
                break
    return regions


def _components(mask, min_frac=0.0):
    """Connected components of a boolean mask: list of (x0, y0, x1, y1, pixel_count)."""
    import numpy as np
    h, w = mask.shape
    seen = np.zeros_like(mask)
    out = []
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if seen[y, x]:
            continue
        stack = [(y, x)]
        seen[y, x] = True
        x0 = x1 = x
        y0 = y1 = y
        count = 0
        while stack:
            cy, cx = stack.pop()
            count += 1
            x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
            for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if (x1 - x0 + 1) * (y1 - y0 + 1) >= min_frac * w * h:
            out.append((x0, y0, x1, y1, count))
    return out


def _grow(mask, r):
    import numpy as np
    out = mask.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def raster_regions(page):
    """Candidate handouts on a page that is one picture (scan or image file), found on a
    low-resolution render: first rectangular dark frames (boxed handouts), otherwise blocks of
    content separated by background."""
    try:
        import numpy as np
    except ImportError:
        sys.exit("numpy is required for image pages: pip install numpy")
    f = fitz()
    scale = 700 / max(page.rect.width, page.rect.height)
    pix = page.get_pixmap(matrix=f.Matrix(scale, scale), colorspace=f.csRGB, alpha=False)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3).astype(int)
    h, w = a.shape[:2]

    def to_rects(boxes):
        rects = [f.Rect(x0 / scale, y0 / scale, (x1 + 1) / scale, (y1 + 1) / scale) for x0, y0, x1, y1 in boxes]
        return [r for r in rects if not any(o != r and o.contains(r) for o in rects)]

    # 1) frames: dark components whose bounding box outline is mostly dark on all four sides
    dark = _grow(a.sum(axis=2) < 250, 1)
    frames = []
    for x0, y0, x1, y1, count in _components(dark, 0.01):
        bw, bh = x1 - x0 + 1, y1 - y0 + 1
        if bw < 20 or bh < 12:
            continue
        sides = [dark[y0:y0 + 3, x0:x1 + 1].any(axis=0).mean(), dark[y1 - 2:y1 + 1, x0:x1 + 1].any(axis=0).mean(),
                 dark[y0:y1 + 1, x0:x0 + 3].any(axis=1).mean(), dark[y0:y1 + 1, x1 - 2:x1 + 1].any(axis=1).mean()]
        if min(sides) > 0.85 and count < 0.6 * bw * bh:  # an outline, not a solid picture
            frames.append((x0, y0, x1, y1))
    if len(frames) >= 2:
        return [{"rect": r, "xrefs": set()} for r in to_rects(frames)]
    # 2) blocks: content that differs from the background (estimated from the page border)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    content = _grow(np.abs(a - np.median(border, axis=0)).sum(axis=2) > 90, 3)
    blocks = [(x0, y0, x1, y1) for x0, y0, x1, y1, count in _components(content, 0.02)
              if count >= 0.5 * (x1 - x0 + 1) * (y1 - y0 + 1) and (x1 - x0 + 1) * (y1 - y0 + 1) < 0.95 * w * h]
    return [{"rect": r, "xrefs": set()} for r in to_rects(blocks)]


def find_regions(path, n, raster=None, lang=None):
    """Return (doc, page, regions, labels, is_raster). Each region gets its labels, text and rotation."""
    doc, page = get_page(path, n)
    textpage = None
    regions = [] if raster else vector_regions(path, doc, page)
    whole = len(regions) == 1 and regions[0]["rect"].width * regions[0]["rect"].height > 0.9 * page.rect.width * page.rect.height
    is_raster = bool(raster) or (not regions or whole) and not page.get_text().strip()  # scan or image file
    if is_raster:
        regions = raster_regions(page)
        try:  # OCR to find the labels and text of an image page
            textpage = page.get_textpage_ocr(language=lang or ocr_lang(path), dpi=200, full=True)
        except Exception:
            textpage = None
    lines = text_lines(page, textpage)
    labels = [l for l in lines if LABEL_RE.match(l["text"])]
    for r in regions:
        r["labels"], r["lines"] = [], []
    for l in labels:  # each label names its nearest region (inside it or right next to it)
        near = sorted(regions, key=lambda r: (rdist(r["rect"], l["rect"]), r["rect"].width * r["rect"].height))
        if near and rdist(near[0]["rect"], l["rect"]) < 60:
            near[0]["labels"].append(l)
            l["region"] = near[0]
    for l in lines:
        c = (l["rect"].tl + l["rect"].br) / 2
        inside = [r for r in regions if c in r["rect"]]
        if inside:
            min(inside, key=lambda r: r["rect"].width * r["rect"].height)["lines"].append(l)
    for r in regions:  # orientation: from the handout's own text, else from its label
        weight = {}
        for l in r["lines"]:
            if l not in r["labels"] and not re.fullmatch(r"\d{1,3}", l["text"]):
                rot = dir_rotation(l["dir"])
                weight[rot] = weight.get(rot, 0) + len(l["text"])
        if weight and max(weight.values()) >= 40:
            r["rot"] = max(weight, key=weight.get)
        else:
            r["rot"] = dir_rotation(r["labels"][0]["dir"]) if r["labels"] else 0
    order = sorted(regions, key=lambda r: (round(r["rect"].y0 / 40), r["rect"].x0))
    return doc, page, order, labels, is_raster


def frac(rect, page):
    W, H = page.rect.width, page.rect.height
    return "x %.2f-%.2f y %.2f-%.2f" % (rect.x0 / W, rect.x1 / W, rect.y0 / H, rect.y1 / H)


def out_name(path, n, suffix):
    os.makedirs(os.path.join(LIBRARY, "renders"), exist_ok=True)
    name = re.sub(r"[^\w.-]+", "_", os.path.splitext(os.path.basename(path))[0])
    return os.path.join(LIBRARY, "renders", "%s_p%d%s.png" % (name, int(n), suffix))


def parse_opts(opts):
    o = {"dpi": 200, "flags": set()}
    it = iter(opts)
    for a in it:
        if a.isdigit():
            o["dpi"] = int(a)
        elif a in ("--region", "--near", "--rect", "--rotate", "--pad", "--lang"):
            o[a[2:]] = next(it, None)
        elif a.startswith("--"):
            o["flags"].add(a[2:])
        else:
            sys.exit("unknown option: %s" % a)
    return o


def regions_cmd(pdf, n, *opts):
    o = parse_opts(opts)
    path = resolve(pdf)
    f = fitz()
    doc, page, regions, labels, is_raster = find_regions(path, n, "raster" in o["flags"], o.get("lang"))
    W, H = page.rect.width, page.rect.height
    print("page %s (%dx%d pt)%s: %d region(s)" % (n, W, H, ", image page (OCR labels)" if is_raster else "",
                                                 len(regions)))
    for i, r in enumerate(regions, 1):
        names = "; ".join(l["text"] for l in r["labels"]) or "-"
        sample = " / ".join(l["text"] for l in r["lines"] if l not in r["labels"])[:90]
        print("  [%d] %s  rot %d  label: %s" % (i, frac(r["rect"], page), r["rot"], names))
        if sample:
            print("      text: %s" % sample)
    loose = [l["text"] for l in labels if "region" not in l]
    if loose:
        print("  labels not attached to a region: %s" % "; ".join(loose))
    # annotated preview: numbered boxes over the page and a 10% grid for --rect
    for i in range(1, 10):
        page.draw_line((W * i / 10, 0), (W * i / 10, H), color=(0.2, 0.6, 1), width=0.4, dashes="[2] 2")
        page.draw_line((0, H * i / 10), (W, H * i / 10), color=(0.2, 0.6, 1), width=0.4, dashes="[2] 2")
        page.insert_text((W * i / 10 + 1, 8), ".%d" % i, fontsize=7, color=(0.2, 0.6, 1))
        page.insert_text((1, H * i / 10 - 1), ".%d" % i, fontsize=7, color=(0.2, 0.6, 1))
    for i, r in enumerate(regions, 1):
        page.draw_rect(r["rect"], color=(1, 0, 0), width=2)
        box = f.Rect(r["rect"].x0, r["rect"].y0, r["rect"].x0 + 22, r["rect"].y0 + 18)
        page.draw_rect(box, color=(1, 0, 0), fill=(1, 0, 0))
        page.insert_text((box.x0 + 4, box.y0 + 14), str(i), fontsize=14, color=(1, 1, 1))
    out = out_name(path, n, "_regions")
    page.get_pixmap(dpi=int(o.get("dpi") if "dpi" in o and o["dpi"] != 200 else 80)).save(out)
    print("preview: %s" % os.path.relpath(out, ROOT))


def hide_label_boxes(page, labels):
    """Remove small filled boxes drawn behind label text (e.g. a translucent caption plate)."""
    f = fitz()
    boxes = [d["rect"] for d in page.get_drawings() if d.get("fill") is not None and
             any(d["rect"].contains(l) and d["rect"].width * d["rect"].height < 6 * l.width * l.height + 2000
                 for l in labels)]
    if boxes:
        for r in boxes:
            page.add_redact_annot(r + (-1, -1, 1, 1), fill=False, cross_out=False)
        page.apply_redactions(images=f.PDF_REDACT_IMAGE_NONE, graphics=f.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED,
                              text=f.PDF_REDACT_TEXT_REMOVE)


def hide(page, rects, is_raster, pix_sample=None):
    """Remove label/foreign text: redact it on vector pages (images underneath stay intact), paint
    it over with the surrounding color on image pages."""
    f = fitz()
    if not rects:
        return
    if is_raster:
        for r in rects:
            ring = f.Rect(r.x0 - 4, r.y0 - 4, r.x1 + 4, r.y1 + 4) & page.rect
            color = pix_sample(ring) if pix_sample else (1, 1, 1)
            page.draw_rect(r + (-1, -1, 1, 1), color=None, fill=color)
    else:
        for r in rects:
            page.add_redact_annot(r + (0.5, 0.5, -0.5, -0.5), fill=False, cross_out=False)
        page.apply_redactions(images=f.PDF_REDACT_IMAGE_NONE, graphics=f.PDF_REDACT_LINE_ART_NONE,
                              text=f.PDF_REDACT_TEXT_REMOVE)


def render(pdf, n, *opts):
    o = parse_opts(opts)
    f = fitz()
    path = resolve(pdf)
    flags = o["flags"]
    pad = float(o.get("pad") or 4)
    rot = 0
    clip = None
    suffix = ""
    if "region" in o or "near" in o or "crop" in flags:
        doc, page, regions, labels, is_raster = find_regions(path, n, "raster" in flags, o.get("lang"))
        if not regions:
            sys.exit("no regions found on this page; use --rect (see `regions` for a grid preview)")
        if "region" in o:
            k = int(o["region"])
            if not 1 <= k <= len(regions):
                sys.exit("region out of range (1..%d)" % len(regions))
            chosen = [regions[k - 1]]
            suffix = "_r%d" % k
        elif "near" in o:
            q = o["near"].lower()
            chosen = [r for r in regions if any(q in l["text"].lower() for l in r["labels"])]
            if not chosen:  # fall back to any text inside a region (e.g. a newspaper headline)
                chosen = [r for r in regions if any(q in l["text"].lower() for l in r["lines"])]
            if not chosen:
                sys.exit("no region labeled or containing %r; run `regions` to see them" % o["near"])
            chosen = chosen[:1]
            suffix = "_" + re.sub(r"\W+", "_", o["near"]).strip("_")[:30]
        else:  # --crop: every handout region on the page, margins dropped
            chosen = regions
            suffix = "_crop"
        target = f.Rect(chosen[0]["rect"])
        for r in chosen[1:]:
            target |= r["rect"]
        rot = chosen[0]["rot"] if len(chosen) == 1 else 0
        pix_sample = None
        if is_raster:
            import numpy as np
            low = page.get_pixmap(dpi=72, colorspace=f.csRGB, alpha=False)
            arr = np.frombuffer(low.samples, dtype=np.uint8).reshape(low.height, low.width, 3)
            sx, sy = low.width / page.rect.width, low.height / page.rect.height

            def pix_sample(ring):
                x0, y0 = int(ring.x0 * sx), int(ring.y0 * sy)
                x1, y1 = max(int(ring.x1 * sx), x0 + 1), max(int(ring.y1 * sy), y0 + 1)
                edge = np.concatenate([arr[y0, x0:x1], arr[y1 - 1, x0:x1], arr[y0:y1, x0], arr[y0:y1, x1 - 1]])
                return tuple(float(v) / 255 for v in np.median(edge, axis=0))
        drop = []
        if "keep-labels" not in flags:
            drop += [l["rect"] for l in labels if l["rect"].intersects(target)]
            if not is_raster:
                hide_label_boxes(page, [l["rect"] for l in labels if l["rect"].intersects(target)])
        H = page.rect.height
        for l in text_lines(page) if not is_raster and "keep-labels" not in flags else []:
            # page numbers printed over or next to the handout
            if re.fullmatch(r"\d{1,3}", l["text"]) and l["rect"].intersects(target) and \
                    (l["rect"].y0 < 60 or l["rect"].y1 > H - 60 or l["dir"][1]):
                drop.append(l["rect"])
        if len(chosen) == 1 and "no-isolate" not in flags:
            region = chosen[0]
            others = [r for r in regions if r is not region and r["rect"].intersects(target)]
            if not is_raster:  # hide overlapping images of other handouts...
                for r in others:
                    for x in r["xrefs"] - region["xrefs"]:
                        page.delete_image(x)
            for r in others:  # ...and their text
                drop += [l["rect"] for l in r["lines"]]
            if not is_raster:  # body text of the book that crosses into the crop (Keeper text)
                inner = region["rect"] + (-3, -3, 3, 3)
                for l in text_lines(page):
                    if l["rect"].intersects(target) and not inner.contains(l["rect"]):
                        drop.append(l["rect"])
        hide(page, drop, is_raster, pix_sample)
        clip = (target + (-pad, -pad, pad, pad)) & page.rect
    else:
        doc, page = get_page(path, n)
    if "rect" in o:
        vals = [float(v) for v in o["rect"].split(",")]
        if len(vals) != 4:
            sys.exit("--rect needs x0,y0,x1,y1 (fractions 0-1 of the page, or points)")
        if max(vals) <= 1:
            W, H = page.rect.width, page.rect.height
            vals = [vals[0] * W, vals[1] * H, vals[2] * W, vals[3] * H]
        clip = f.Rect(vals) & page.rect
        suffix = suffix or "_rect"
    if "rotate" in o:
        rot = int(o["rotate"]) % 360
    mat = f.Matrix(o["dpi"] / 72, o["dpi"] / 72).prerotate(rot)
    out = out_name(path, n, suffix)
    page.get_pixmap(matrix=mat, clip=clip, alpha=False).save(out)
    print(os.path.relpath(out, ROOT) + ("  (rotated %d)" % rot if rot else ""))
    if clip is None and not page.get_text().strip():
        print("note: this page has no text layer: a scan, or a full-page illustration "
              "(chapter openers are; the text is usually on the next page)")


def images(pdf, n):
    f = fitz()
    path = resolve(pdf)
    doc = f.open(path)
    n = int(n)
    if not 1 <= n <= doc.page_count:
        sys.exit("page out of range (1..%d)" % doc.page_count)
    os.makedirs(os.path.join(LIBRARY, "renders"), exist_ok=True)
    name = re.sub(r"[^\w.-]+", "_", os.path.splitext(os.path.basename(path))[0])
    saved = 0
    for k, img in enumerate(doc[n - 1].get_images(full=True), 1):
        xref, smask = img[0], img[1]
        if img[2] < 200 or img[3] < 200:
            continue  # skip icons, ornaments, and thin strips
        data = None
        if smask:  # image with a transparency mask: composite it when sizes match
            try:
                pix = f.Pixmap(f.Pixmap(doc, xref), f.Pixmap(doc, smask))
                data, ext = pix.tobytes("png"), "png"
            except Exception:
                data = None
        if data is None:
            info_ = doc.extract_image(xref)
            data, ext = info_["image"], info_["ext"]
        out = os.path.join(LIBRARY, "renders", "%s_p%d_img%d.%s" % (name, n, k, ext))
        with open(out, "wb") as fh:
            fh.write(data)
        print("%s  (%dx%d)" % (os.path.relpath(out, ROOT), img[2], img[3]))
        saved += 1
    if not saved:
        print("no large embedded images on this page; use `render` instead")


def info(pdf):
    path = resolve(pdf)
    doc = fitz().open(path)
    empty = sum(1 for p in doc if not page_ok(p.get_text("text")))
    print("pages: %d, pages with usable text: %d" % (doc.page_count, doc.page_count - empty))
    print("bookmarks: %d" % len(doc.get_toc()))
    tp = text_path(path)
    print("text: %s%s" % (os.path.relpath(tp, ROOT), "" if os.path.exists(tp) else " (not extracted)"))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return
    cmd, args = argv[1], argv[2:]
    if cmd == "extract":
        extract(args)
    elif cmd == "search" and args:
        search(args[0], args[1] if len(args) > 1 else None)
    elif cmd == "toc" and args:
        toc(args[0])
    elif cmd == "pages" and len(args) == 2:
        pages(args[0], args[1])
    elif cmd == "render" and len(args) >= 2:
        render(*args)
    elif cmd == "regions" and len(args) >= 2:
        regions_cmd(*args)
    elif cmd == "images" and len(args) == 2:
        images(args[0], args[1])
    elif cmd == "info" and args:
        info(args[0])
    else:
        print(__doc__)


if __name__ == "__main__":
    main(sys.argv)
