# Arvind Karunakaran — Academic Website

A [Quarto](https://quarto.org) website for Arvind Karunakaran (Stanford
University). Clean, typography-first, static output. Deploys to GitHub Pages
(`gh-pages` branch) on every push to `main`.

## Prerequisites

- [Quarto](https://quarto.org/docs/get-started/) (v1.4+)
- Python 3 (only for the `scripts/add_paper.py` helper — the site itself
  renders without it)

## Preview locally

```bash
quarto preview
```

This serves the site with live reload at `http://localhost:port`. To do a
one-off full build into `_site/`:

```bash
quarto render
```

## Project layout

```
_quarto.yml          Site config: nav, footer, theme, OpenGraph
theme.scss           Design system (palette, typography, components)
styles.css           Small extra CSS overrides
build-date.lua       Injects the render date into the footer ("Last updated")
index.qmd            Home
research.qmd         Research statement + areas/topics
publications.qmd     Publications (renders from papers.yml — do not hardcode)
teaching.qmd         Courses + syllabus links
people.qmd           Doctoral & master's advisees
cv.qmd               Embedded CV PDF + honors/education
news.qmd             Reverse-chronological updates
contact.qmd          Email, ORCID, Scholar, address
papers.yml           SINGLE SOURCE OF TRUTH for publications
_templates/
  publications.ejs   Custom listing template (year grouping, DOI/PDF, badges)
files/
  papers/            Paper PDFs   (e.g. 2024-asq-obscured-accountability.pdf)
  syllabi/           Syllabi      (e.g. msande180-spring2026.pdf)
  cv/cv.pdf          The CV — ALWAYS this filename so links never break
  misc/              Slides, media, appendices
images/              favicon.svg, profile placeholder, OG image
scripts/add_paper.py Helper to add a paper (+ copy its PDF)
.github/workflows/publish.yml   Auto-deploy on push to main
CNAME                Custom-domain placeholder (edit before going live)
```

## Common tasks

### Add a publication

Publications live **only** in `papers.yml`. Either add a one-item block by hand
(copy an existing entry and edit the fields — see the header comment in
`papers.yml`), or use the helper:

```bash
python scripts/add_paper.py \
  --title "Paper Title" \
  --authors "Karunakaran, A., Coauthor, B." \
  --year 2025 --venue "Organization Science" \
  --volume 36 --issue 2 --pages "1-20" \
  --doi 10.1287/orsc.2025.xxxx \
  --pdf ~/Downloads/paper.pdf        # optional; copied + auto-named
```

Add `--equal` for equal-contribution papers, and
`--type "Book Chapter"` or `--type "Working Paper"` to change the section.
Matching is by DOI: an existing DOI is updated in place, otherwise appended.
Then run `quarto render` (or keep `quarto preview` running).

### Add a syllabus

1. Drop the PDF in `files/syllabi/`, named `msandeNNN-termYEAR.pdf`
   (e.g. `msande180-spring2026.pdf`).
2. Link it from `teaching.qmd`:
   `[Syllabus (PDF)](files/syllabi/msande180-spring2026.pdf){.no-underline .pub-links}`

### Update the CV

Replace `files/cv/cv.pdf`. **Keep the filename `cv.pdf`** so the link on the CV
page never breaks. No other edits needed.

### Post news

Edit `news.qmd` and add a new item at the **top** of the list. Copy the format
of an existing entry (a `.news-date` block followed by a `.news-body` block).
Optionally mirror the biggest items on the Home page (`index.qmd`).

### Replace the photo / favicon / social image

- Home photo: replace `images/profile-placeholder.svg` (or add
  `images/profile.jpg` and point `index.qmd` at it).
- Favicon: `images/favicon.svg`.
- Social preview: `images/og-image.png` — a real 1200×630 PNG renders best on
  social platforms.

## Deploy

Pushing to `main` triggers `.github/workflows/publish.yml`, which renders the
site and publishes it to the `gh-pages` branch (equivalent to
`quarto publish gh-pages`). In the repo's **Settings → Pages**, set the source
to the `gh-pages` branch.

### Custom domain

1. Edit `CNAME` to your domain (e.g. `www.yourdomain.edu`).
2. Set `site-url` in `_quarto.yml` to the same domain (used for OpenGraph URLs).
3. Configure the DNS record with your domain registrar.

## License / content

Site content © Arvind Karunakaran. Built with Quarto.
