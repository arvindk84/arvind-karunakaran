# Arvind Karunakaran: personal website

Source for [www.arvindkarunakaran.com](https://www.arvindkarunakaran.com): plain HTML and CSS, published to GitHub Pages. The site has two registers that share one design. The academic pages (research, publications, CV) are quiet and text-led. The Speaking & Advising page is built for event organizers, with signature talks, video, formats, clients, an organizer kit, and an enquiry link.

## Preview locally

```bash
pip install pyyaml
python scripts/build_site.py --out _site
python -m http.server 8000 --directory _site
```

Then open http://localhost:8000.

## Project layout

```
index.html … news.html   Pages (edit these directly, except the generated blocks)
publications.html,
teaching.html, people.html   Redirect stubs for old URLs
404.html                  Not-found page
css/site.css              Design system
js/site.js                Small progressive enhancements
fonts/                    Self-hosted Manrope, Inter, IBM Plex Mono
partials/                 Shared header and footer (copied into every page by the build)
papers.yml                SINGLE SOURCE OF TRUTH for publications
scripts/build_site.py     Renders papers.yml → research.html, syncs partials, assembles _site/
scripts/check_site.py     Link and page checks
scripts/add_paper.py      Helper to add a paper (+ copy its PDF)
files/                    Hosted PDFs: papers/, syllabi/, cv/cv.pdf, misc/
images/                   Photos, logos, favicon, social cards
.github/workflows/publish.yml   Build, check, and publish to gh-pages on every push to main
```

Legacy Quarto sources (`*.qmd`, `_quarto.yml`, `theme.scss`, `styles.css`, `build-date.lua`, `_templates/`) are kept for reference only. They are no longer built.

## Common tasks

**Add a publication:** `python scripts/add_paper.py --title "…" --authors "Karunakaran, A., Coauthor, B." --year 2026 --venue "…" --doi 10.xxxx/… [--pdf ~/Downloads/paper.pdf] [--equal]`, or edit `papers.yml`. Then run `python scripts/build_site.py` and commit `papers.yml` and `research.html`.

**Update the CV:** replace `files/cv/cv.pdf`. Keep the filename.

**Post news:** add an item at the top of `news.html`, and mirror the newest three on `index.html`.

**Change the nav or footer:** edit `partials/header.html` or `partials/footer.html`, then run `python scripts/build_site.py`.

## Deploy

Every push to `main` runs `.github/workflows/publish.yml`. The workflow builds `_site/`, fails if `check_site.py` finds broken links, and publishes `_site/` to the `gh-pages` branch. In **Settings → Pages**, the source stays **Deploy from a branch: `gh-pages`**. The `CNAME` file keeps the custom domain.

Site content © Arvind Karunakaran.
