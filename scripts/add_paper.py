#!/usr/bin/env python3
"""
add_paper.py — add (or update) a publication in papers.yml and, optionally,
copy its PDF into files/papers/ using the site's naming convention.

This keeps papers.yml as the single source of truth for the Publications page.
It uses no third-party libraries (pure text handling), so the header comments
and formatting in papers.yml are preserved.

Examples
--------
Add a paper and copy its PDF (auto-named 2024-asq-frontline-professionals.pdf):

    python scripts/add_paper.py \\
        --title "Frontline Professionals in the Wake of Social Media Scrutiny" \\
        --authors "Karunakaran, A." \\
        --year 2024 --venue "Administrative Science Quarterly" \\
        --volume 69 --issue 3 --pages "747-790" \\
        --doi 10.1177/00018392241256303 \\
        --pdf ~/Downloads/asq-paper.pdf

Add a co-authored, equal-contribution paper without a PDF:

    python scripts/add_paper.py \\
        --title "Artificial Intelligence at Work" \\
        --authors "Karunakaran, A., Lebovitz, S., Narayanan, D., Rahman, H." \\
        --year 2025 --venue "Academy of Management Annals" \\
        --doi 10.5465/annals.2023.0230 --equal

Matching is by DOI: if a DOI already exists in papers.yml the entry is replaced
(update); otherwise it is appended (add).
"""

import argparse
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS_YML = os.path.join(ROOT, "papers.yml")
PAPERS_DIR = os.path.join(ROOT, "files", "papers")

# Common venue -> short token used in filenames.
VENUE_ABBREV = {
    "administrative science quarterly": "asq",
    "organization science": "orgsci",
    "academy of management journal": "amj",
    "academy of management annals": "annals",
    "academy of management review": "amr",
    "research policy": "respol",
    "organization theory": "orgtheory",
    "strategic organization": "stratorg",
    "journal of management inquiry": "jmi",
    "journal of the american society for information science and technology": "jasist",
}

STOPWORDS = {"the", "a", "an", "of", "and", "on", "in", "to", "for", "how",
             "with", "at", "by", "as", "into", "examining"}


def slugify(text, max_words=4):
    words = re.sub(r"[^a-z0-9\s-]", "", text.lower()).split()
    keep = [w for w in words if w not in STOPWORDS] or words
    return "-".join(keep[:max_words])


def venue_token(venue):
    key = venue.lower().strip()
    if key in VENUE_ABBREV:
        return VENUE_ABBREV[key]
    first = re.sub(r"[^a-z0-9]", "", venue.lower().split()[0]) if venue else "paper"
    return first or "paper"


def make_filename(args):
    if args.name:
        return args.name if args.name.endswith(".pdf") else args.name + ".pdf"
    return f"{args.year}-{venue_token(args.venue)}-{slugify(args.title)}.pdf"


def q(s):
    """Quote a YAML string value, escaping embedded double quotes."""
    return '"' + str(s).replace('"', "'") + '"'


def build_entry(args, pdf_name):
    ptype = args.type
    lines = [
        f"- title: {q(args.title)}",
        f"  author: {q(args.authors)}",
        f"  year: {args.year}",
        f"  venue: {q(args.venue)}",
    ]
    if args.volume:
        lines.append(f"  volume: {args.volume}")
    if args.issue:
        lines.append(f"  issue: {args.issue}")
    if args.pages:
        lines.append(f"  pages: {q(args.pages)}")
    if args.doi:
        lines.append(f"  doi: {args.doi}")
    if pdf_name:
        lines.append(f"  pdf: {pdf_name}")
    if args.equal:
        lines.append("  equal: true")
    lines.append(f"  type: {q(ptype)}")
    lines.append(f'  categories: [{q(ptype)}]')
    date = args.date or f"{args.year}-01-01"
    lines.append(f"  date: {q(date)}")
    return "\n".join(lines) + "\n"


def split_entries(body):
    """Split the entry region of papers.yml into (header, [entry_blocks])."""
    # Header = everything before the first top-level list item.
    m = re.search(r"^- ", body, flags=re.MULTILINE)
    if not m:
        return body, []
    header = body[: m.start()]
    rest = body[m.start():]
    # Each entry starts at a line beginning with "- ".
    parts = re.split(r"(?m)^(?=- )", rest)
    entries = [p for p in parts if p.strip()]
    return header, entries


def main():
    p = argparse.ArgumentParser(description="Add or update a paper in papers.yml.")
    p.add_argument("--title", required=True)
    p.add_argument("--authors", required=True,
                   help='Full author string, e.g. "Karunakaran, A., Rahman, H."')
    p.add_argument("--year", required=True, type=int)
    p.add_argument("--venue", required=True, help="Journal or book title.")
    p.add_argument("--volume")
    p.add_argument("--issue")
    p.add_argument("--pages")
    p.add_argument("--doi")
    p.add_argument("--type", default="Journal Article",
                   choices=["Journal Article", "Book Chapter", "Working Paper"])
    p.add_argument("--equal", action="store_true",
                   help="Mark as an equal-contribution paper.")
    p.add_argument("--date", help="YYYY-MM-DD for sorting (default: <year>-01-01).")
    p.add_argument("--pdf", help="Path to a source PDF to copy into files/papers/.")
    p.add_argument("--name", help="Override the generated PDF filename.")
    args = p.parse_args()

    # 1) Handle the PDF copy (if any).
    pdf_name = None
    if args.pdf:
        src = os.path.expanduser(args.pdf)
        if not os.path.isfile(src):
            sys.exit(f"ERROR: PDF not found: {src}")
        pdf_name = make_filename(args)
        os.makedirs(PAPERS_DIR, exist_ok=True)
        dst = os.path.join(PAPERS_DIR, pdf_name)
        shutil.copy2(src, dst)
        print(f"Copied PDF -> files/papers/{pdf_name}")

    entry = build_entry(args, pdf_name)

    # 2) Read papers.yml, add or update by DOI.
    with open(PAPERS_YML, "r", encoding="utf-8") as f:
        body = f.read()
    header, entries = split_entries(body)

    action = "Added"
    if args.doi:
        doi_needle = f"doi: {args.doi}"
        idx = next((i for i, e in enumerate(entries) if doi_needle in e), None)
        if idx is not None:
            entries[idx] = entry
            action = "Updated"
        else:
            entries.append(entry)
    else:
        entries.append(entry)

    new_body = header.rstrip("\n") + "\n\n" + "\n".join(
        e.rstrip("\n") + "\n" for e in entries)
    with open(PAPERS_YML, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_body)

    print(f"{action} entry in papers.yml: \"{args.title}\" ({args.year})")
    print("Run `quarto render` (or `quarto preview`) to rebuild the site.")


if __name__ == "__main__":
    main()
