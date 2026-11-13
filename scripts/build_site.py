#!/usr/bin/env python3
"""Build the static site.

    python scripts/build_site.py              # update pages in place (publications + header/footer)
    python scripts/build_site.py --out _site  # also assemble the deployable folder

What it does
1. Publications: renders papers.yml (the single source of truth) into research.html,
   between <!-- PUBS:START --> and <!-- PUBS:END -->. Never hand-edit that block.
2. Header and footer: copies partials/header.html and partials/footer.html into every
   page between the HEADER/FOOTER markers and marks the current nav link
   (scripts/sync_partials.py does the same thing on its own).
3. With --out: copies only what the public site needs (pages, css, js, fonts, images,
   files, CNAME) into a fresh folder, adds .nojekyll, and stamps "Last updated <date>"
   into the footer. The GitHub Action runs this and publishes the folder to gh-pages.

Requires PyYAML (pip install pyyaml).
"""
import argparse
import datetime as dt
import html
import pathlib
import re
import shutil
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import sync_partials  # noqa: E402

PUBLIC_DIRS = ["css", "js", "fonts", "images", "files"]
PUBLIC_FILES = ["CNAME"]
SITE_URL = "https://www.arvindkarunakaran.com/"
TYPE_SLUG = {"Journal Article": "article", "Book Chapter": "chapter", "Working Paper": "working"}
FILTER_LABEL = {"article": "Journal articles", "chapter": "Book chapters", "working": "Working papers"}
ME = "Karunakaran, A."


def esc(s):
    return html.escape(str(s), quote=True)


def render_pub(p):
    for key in ("title", "author", "year", "venue", "type"):
        if not p.get(key):
            raise SystemExit(f"papers.yml: entry is missing '{key}': {p.get('title', p)}")
    slug = TYPE_SLUG.get(p["type"])
    if not slug:
        raise SystemExit(f"papers.yml: unknown type '{p['type']}' for {p['title']}")
    doi = str(p.get("doi") or "").strip()
    pdf = str(p.get("pdf") or "").strip()
    if pdf and not (ROOT / "files" / "papers" / pdf).exists():
        raise SystemExit(f"papers.yml: pdf not found in files/papers/: {pdf}")
    href = f"https://doi.org/{doi}" if doi else (f"files/papers/{pdf}" if pdf else "")

    title = esc(p["title"])
    title_html = f'<a href="{esc(href)}">{title}</a>' if href else title
    authors = esc(p["author"]).replace(esc(ME), f'<span class="me">{esc(ME)}</span>')

    meta = ""
    if p.get("volume"):
        meta = str(p["volume"]) + (f"({p['issue']})" if p.get("issue") else "")
    if p.get("pages"):
        meta += (", " if meta else "") + str(p["pages"])
    venue = f"<em>{esc(p['venue'])}</em>" + (f", {esc(meta)}" if meta else "")

    chips = []
    if doi:
        chips.append(f'<a class="chip" href="https://doi.org/{esc(doi)}">DOI</a>')
    if pdf:
        chips.append(f'<a class="chip" href="files/papers/{esc(pdf)}">PDF</a>')
    if p.get("equal"):
        chips.append('<span class="chip chip--note">Equal contribution</span>')
    if slug == "chapter":
        chips.append('<span class="chip chip--note">Book chapter</span>')
    if slug == "working":
        chips.append('<span class="chip chip--note">Working paper</span>')
    note = f'\n            <p class="pub-note">{esc(p["note"])}</p>' if p.get("note") else ""

    # Optional `status` (e.g. "Forthcoming") replaces the year label for accepted, not-yet-issued papers.
    year_label = esc(p["status"]) if p.get("status") else esc(p["year"])

    return f"""        <li class="pub" data-type="{slug}">
          <div class="pub-year">{year_label}</div>
          <div>
            <h3 class="pub-title">{title_html}</h3>
            <p class="pub-authors">{authors}</p>
            <p class="pub-venue">{venue}</p>
            <div class="chips">{''.join(chips)}</div>{note}
          </div>
        </li>"""


def render_publications(papers):
    # Newest first: forthcoming (has `status`) on top, then by year, then by date within the year.
    papers = sorted(papers, key=lambda p: (1 if p.get("status") else 0, int(p["year"]), str(p.get("date") or p["year"])), reverse=True)
    present = []
    for p in papers:
        s = TYPE_SLUG.get(p.get("type"))
        if s and s not in present:
            present.append(s)
    order = [s for s in ("article", "chapter", "working") if s in present]
    buttons = ['        <button class="filter" type="button" data-filter="all" aria-pressed="true">All</button>']
    buttons += [f'        <button class="filter" type="button" data-filter="{s}" aria-pressed="false">{FILTER_LABEL[s]}</button>' for s in order]
    return (
        "<!-- PUBS:START (generated from papers.yml by scripts/build_site.py; do not edit by hand) -->\n"
        '      <div class="filters" role="group" aria-label="Filter publications" data-filter-group="pub-list">\n'
        + "\n".join(buttons)
        + "\n      </div>\n\n      <ol class=\"pubs\" id=\"pub-list\">\n"
        + "\n".join(render_pub(p) for p in papers)
        + "\n      </ol>\n      <!-- PUBS:END -->"
    )


def update_research(root):
    page = root / "research.html"
    papers = yaml.safe_load((root / "papers.yml").read_text(encoding="utf-8")) or []
    src = page.read_text(encoding="utf-8")
    pat = re.compile(r"<!-- PUBS:START.*?<!-- PUBS:END -->", re.S)
    if not pat.search(src):
        raise SystemExit("research.html: PUBS markers not found")
    out = pat.sub(lambda _: render_publications(papers), src, count=1)
    if out != src:
        page.write_text(out, encoding="utf-8")
    print(f"  publications: {len(papers)} entries rendered into research.html")


def assemble(root, out, date_text):
    out = (root / out).resolve() if not pathlib.Path(out).is_absolute() else pathlib.Path(out).resolve()
    if out == root or out in root.parents:
        raise SystemExit("--out must be a separate folder, e.g. _site")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    pages = sorted(root.glob("*.html"))
    for page in pages:
        s = page.read_text(encoding="utf-8")
        s = s.replace("<!-- BUILD-DATE -->", f'<span class="build-date">Last updated {date_text}</span>')
        (out / page.name).write_text(s, encoding="utf-8")
    for d in PUBLIC_DIRS:
        if (root / d).exists():
            shutil.copytree(root / d, out / d, ignore=shutil.ignore_patterns(".gitkeep", ".DS_Store", "Thumbs.db"))
    for f in PUBLIC_FILES:
        if (root / f).exists():
            shutil.copy2(root / f, out / f)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    write_sitemap(out, pages)
    print(f"  assembled {len(pages)} pages into {out} (Last updated {date_text})")


def write_sitemap(out, pages):
    """sitemap.xml + robots.txt for the real pages (skips redirect stubs and 404)."""
    urls = []
    for page in pages:
        s = page.read_text(encoding="utf-8")
        if page.name == "404.html" or 'http-equiv="refresh"' in s:
            continue
        loc = SITE_URL + ("" if page.name == "index.html" else page.name)
        urls.append(f"  <url><loc>{loc}</loc></url>")
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>\n",
        encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="assemble the deployable site into this folder (e.g. _site)")
    args = ap.parse_args()
    update_research(ROOT)
    sync_partials.main(str(ROOT))
    if args.out:
        today = dt.date.today()
        assemble(ROOT, args.out, f"{today:%B} {today.day}, {today.year}")


if __name__ == "__main__":
    main()
