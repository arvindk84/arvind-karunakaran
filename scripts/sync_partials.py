#!/usr/bin/env python3
"""Copy the shared header and footer into every page, and mark the current nav link.

Usage:
    python sync_partials.py <site_dir>

How it works
- Each page has two marker pairs:
      <!-- HEADER:START --> ... <!-- HEADER:END -->
      <!-- FOOTER:START --> ... <!-- FOOTER:END -->
  Everything between a pair is replaced by partials/header.html or partials/footer.html.
- The current nav item comes from <body data-nav="research.html">. Pages that are not in
  the main nav (news.html, redirects) can point at a parent, or at a file that is not in
  the nav, in which case no link is marked.
- Run it after any change to the nav, footer, or partials. It is safe to run repeatedly.

Why: the site has no build step, so the header and footer are repeated in every file.
This script keeps one source of truth without adding a framework.
"""
import pathlib
import re
import sys

HEADER_RE = re.compile(r"<!-- HEADER:START -->.*?<!-- HEADER:END -->", re.S)
FOOTER_RE = re.compile(r"<!-- FOOTER:START -->.*?<!-- FOOTER:END -->", re.S)
NAV_RE = re.compile(r'(<nav class="nav"[^>]*>)(.*?)(</nav>)', re.S)


def mark_current(header: str, current: str) -> str:
    def fix_nav(m):
        body = re.sub(r'\s+aria-current="page"', "", m.group(2))
        body = body.replace(f'<a href="{current}">', f'<a href="{current}" aria-current="page">', 1)
        return m.group(1) + body + m.group(3)
    return NAV_RE.sub(fix_nav, header, count=1)


def main(site_dir: str) -> int:
    site = pathlib.Path(site_dir)
    header = (site / "partials" / "header.html").read_text(encoding="utf-8").strip()
    footer = (site / "partials" / "footer.html").read_text(encoding="utf-8").strip()
    changed = 0
    for page in sorted(site.glob("*.html")):
        src = page.read_text(encoding="utf-8")
        if "<!-- HEADER:START -->" not in src:
            print(f"  skip   {page.name} (no markers)")
            continue
        m = re.search(r'<body[^>]*\sdata-nav="([^"]+)"', src)
        current = m.group(1) if m else page.name
        h = mark_current(header, current)
        out = HEADER_RE.sub(lambda _: f"<!-- HEADER:START -->\n{h}\n<!-- HEADER:END -->", src, count=1)
        out = FOOTER_RE.sub(lambda _: f"<!-- FOOTER:START -->\n{footer}\n<!-- FOOTER:END -->", out, count=1)
        if out != src:
            page.write_text(out, encoding="utf-8")
            changed += 1
            print(f"  synced {page.name} (current: {current})")
        else:
            print(f"  ok     {page.name}")
    print(f"{changed} page(s) updated")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
