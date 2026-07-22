# CLAUDE.md — project conventions for Claude Code

This is a **Quarto website** for Arvind Karunakaran (Stanford), deployed to
GitHub Pages (`gh-pages`) with a custom domain. Static output only; no heavy
JS. Read this before making changes.

## Hard rules (do not violate)

- **Never delete files in `/files/`.** They are the hosted PDFs (papers,
  syllabi, CV) that live links point to.
- **Never rename `files/cv/cv.pdf`.** The CV link depends on this exact
  filename. To update the CV, overwrite the file in place.
- **Always update `papers.yml`** to change publications — never edit the
  rendered HTML or hardcode citations into `publications.qmd`. The Publications
  page renders from `papers.yml` via `_templates/publications.ejs`.

## Architecture

- Pages are `.qmd` files at the repo root; site config is `_quarto.yml`.
- Design system lives in `theme.scss` (SCSS variables + component rules);
  small overrides in `styles.css`. Keep the restrained palette: off-white
  `#fbfaf7`, near-black `#1a1a1a`, one accent — Stanford cardinal `#8c1515`.
  Serif body via system font stack (no web-font downloads).
- `build-date.lua` injects the render date into the footer ("Last updated ...").
  Do not hardcode a date in the footer.
- Publications: `papers.yml` (data) → Quarto `listing` in `publications.qmd`
  → `_templates/publications.ejs` (renders year groups, DOI/PDF links,
  Equal Contribution badge). The on-page type filter is vanilla JS inside
  `publications.qmd`.

## Content conventions

### Document folders and naming
- `files/papers/`  → `YYYY-<venue>-<slug>.pdf` (e.g.
  `2024-asq-obscured-accountability.pdf`)
- `files/syllabi/` → `msandeNNN-termYEAR.pdf` (e.g. `msande180-spring2026.pdf`)
- `files/cv/cv.pdf` → the CV, always this name
- `files/misc/`    → everything else (slides, media, appendices)

### papers.yml entry fields
`title` (no trailing period), `author` (full string; `Karunakaran, A.` is
auto-bolded), `year`, `venue` (italicized), optional `volume`/`issue`/`pages`,
`doi` (bare, no URL), optional `pdf` (filename in `files/papers/`), optional
`equal: true`, `type` (`Journal Article` | `Book Chapter` | `Working Paper`),
`categories: [<type>]`, and `date` (`YYYY-MM-DD`, controls sort order).

## How to add content

- **Add a paper:** `python scripts/add_paper.py --title ... --authors ...
  --year ... --venue ... --doi ... [--pdf path] [--equal]
  [--type "Book Chapter"]`. Or hand-edit `papers.yml` (copy an entry). Match is
  by DOI (updates in place, else appends).
- **Add a syllabus:** put the PDF in `files/syllabi/` (naming above), then link
  it from `teaching.qmd`.
- **Update the CV:** overwrite `files/cv/cv.pdf` (same filename).
- **Post news:** add an item at the TOP of the list in `news.qmd`; optionally
  mirror on `index.qmd`.

## Build / verify

- Preview: `quarto preview`. Full build: `quarto render` (outputs to `_site/`).
- After content changes, run `quarto render` and confirm it completes without
  errors before committing.
- Deploy is automatic on push to `main` (`.github/workflows/publish.yml`).

## Placeholders to replace before go-live

- `CNAME` and `site-url` in `_quarto.yml` (custom domain).
- `images/profile-placeholder.svg` (real photo), `images/og-image.png`
  (1200×630), Google Scholar URL in `_quarto.yml` + `contact.qmd`, and the
  office/mail-code line in `contact.qmd`.
