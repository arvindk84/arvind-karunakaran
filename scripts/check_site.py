#!/usr/bin/env python3
"""Static QA for the site: broken internal links and anchors, image hygiene, page metadata,
and placeholder text that should never ship.

Usage:
    python check_site.py <site_dir> [--repo-assets images/,files/]

--repo-assets  Comma-separated path prefixes that live in the deployed repo but may be
               missing from a local build folder (photos, logos, the CV PDF). Missing files
               under these prefixes are reported as warnings, not errors. A warning still
               means "confirm this file exists in the repo before you push".

Exit code is 1 if any error is found.
"""
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

PLACEHOLDER_PATTERNS = [
    r"\bTODO\b", r"\bTKTK\b", r"lorem ipsum", r"example\.com", r"\bXXX\b",
    r'href="DOI-', r'href="PDF-', r'href="#"', r"\[(?:link|url|placeholder)\]",
]


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.imgs = set(), [], []
        self.title, self.in_title = "", False
        self.desc = None
        self.h1 = 0
        self.lang = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "title":
            self.in_title = True
        if tag == "meta" and a.get("name") == "description":
            self.desc = a.get("content", "")
        if tag == "h1":
            self.h1 += 1
        if tag in ("a", "link") and a.get("href"):
            self.links.append((tag, a["href"], self.getpos()[0]))
        if tag in ("img", "script", "source", "iframe") and a.get("src"):
            self.links.append((tag, a["src"], self.getpos()[0]))
        if tag == "img":
            self.imgs.append((a, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    site = pathlib.Path(argv[0])
    repo_assets = []
    if "--repo-assets" in argv:
        repo_assets = [p.strip() for p in argv[argv.index("--repo-assets") + 1].split(",") if p.strip()]

    pages = {}
    for f in sorted(site.glob("*.html")):
        p = Page()
        p.feed(f.read_text(encoding="utf-8"))
        pages[f.name] = (p, f.read_text(encoding="utf-8"))

    errors, warnings = [], []
    for name, (p, raw) in pages.items():
        is_redirect = 'http-equiv="refresh"' in raw
        if not p.title.strip():
            errors.append(f"{name}: missing <title>")
        if not is_redirect:
            if not p.desc:
                errors.append(f"{name}: missing meta description")
            if p.h1 != 1:
                errors.append(f"{name}: expected exactly one <h1>, found {p.h1}")
            if not p.lang:
                errors.append(f"{name}: <html> has no lang attribute")
        for pat in PLACEHOLDER_PATTERNS:
            for m in re.finditer(pat, raw, re.I):
                line = raw.count("\n", 0, m.start()) + 1
                errors.append(f"{name}:{line}: placeholder text '{m.group(0)}'")
        for a, line in p.imgs:
            if "alt" not in a:
                errors.append(f"{name}:{line}: <img> without alt ({a.get('src')})")
            if not (a.get("width") and a.get("height")):
                warnings.append(f"{name}:{line}: <img> without width/height, causes layout shift ({a.get('src')})")

        for tag, url, line in p.links:
            parts = urlsplit(url)
            if parts.scheme in ("http", "https", "mailto", "tel", "data") or url.startswith("//"):
                continue
            path, frag = unquote(parts.path), parts.fragment
            if not path:  # same-page anchor
                if frag and frag not in p.ids and frag != "top":
                    errors.append(f"{name}:{line}: anchor #{frag} not found on this page")
                continue
            path = path.lstrip("/")  # root-relative links (used by 404.html) resolve from the site root
            target = (site / path)
            if not target.exists():
                msg = f"{name}:{line}: missing file {path}"
                (warnings if any(path.startswith(pre) for pre in repo_assets) else errors).append(msg)
                continue
            if frag and target.suffix == ".html":
                tp = pages.get(target.name)
                if tp and frag not in tp[0].ids:
                    errors.append(f"{name}:{line}: {path}#{frag} has no element with that id")

    for w in warnings:
        print("warn  ", w)
    for e in errors:
        print("ERROR ", e)
    print(f"\n{len(pages)} pages · {len(errors)} error(s) · {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
