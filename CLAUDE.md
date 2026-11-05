# CLAUDE.md: project conventions

This is a **static HTML/CSS website** for Arvind Karunakaran (Stanford). On every push to `main`, a GitHub Action builds it and publishes it to the `gh-pages` branch. GitHub Pages serves that branch at www.arvindkarunakaran.com. There is no framework and no build tool beyond one Python script. Read this file before you change anything.

The site moved off Quarto in November 2026. The `.qmd` files, `_quarto.yml`, `theme.scss`, `styles.css`, `build-date.lua`, and `_templates/` are still in the repo for reference. **None of them is built anymore.** Do not edit them to change the site.

## Hard rules (do not violate)

- **Never delete files in `/files/`.** Live links point to these hosted PDFs (papers, syllabi, CV).
- **Never rename `files/cv/cv.pdf`.** To update the CV, overwrite the file in place.
- **Always change publications in `papers.yml`.** `scripts/build_site.py` renders it into `research.html` between `<!-- PUBS:START -->` and `<!-- PUBS:END -->`. Never hand-edit that block.
- **Edit the shared header and footer only in `partials/`,** then run the build. Each page carries a copy between the `HEADER:START/END` and `FOOTER:START/END` markers.
- **Keep the old URLs working.** `publications.html`, `teaching.html`, and `people.html` are redirect stubs. Do not delete them.

## Architecture

| Path | What it is |
|---|---|
| `index.html`, `research.html`, `speaking.html`, `writing.html`, `about.html`, `cv.html`, `contact.html`, `news.html` | Pages. Main nav: Research · Speaking & Advising · Writing & Media · About · CV · Contact. |
| `publications.html`, `teaching.html`, `people.html` | Redirects to `research.html#publications`, `about.html#teaching`, `about.html#students` |
| `404.html` | Not-found page (root-relative links; no partial markers) |
| `css/site.css` | The whole design system. Tokens live in `:root`. |
| `js/site.js` | Small enhancements: mobile menu, publication filters, click-to-load videos, copy buttons, sub-nav scrollspy. Every page works without it. |
| `fonts/` | Self-hosted Manrope, Inter, IBM Plex Mono (woff2, OFL) |
| `partials/header.html`, `partials/footer.html` | The single source for the header and footer |
| `papers.yml` | Single source of truth for publications |
| `scripts/build_site.py` | Renders publications, syncs partials, and (with `--out`) assembles `_site/` with sitemap, robots, `.nojekyll`, and a "Last updated" date |
| `scripts/check_site.py` | Link and page checks (the deploy fails if this fails) |
| `scripts/add_paper.py` | Adds or updates a `papers.yml` entry and copies its PDF |
| `.github/workflows/publish.yml` | Build → check → publish `_site/` to `gh-pages` |

Design: modern minimal sans. Manrope for headings, Inter for body, IBM Plex Mono for small labels. Paper `#FBFAF7`, ink `#15171B`, and one accent, Stanford cardinal `#8C1515`. Academic pages stay quiet. The Speaking & Advising page uses bands, cards, and media. Details and component HTML are in the `academic-speaker-site` skill.

## Content conventions

- File naming: `files/papers/YYYY-<venue>-<slug>.pdf`, `files/syllabi/msandeNNN-termYEAR.pdf`, `files/cv/cv.pdf`, `files/misc/` for everything else.
- `papers.yml` fields: `title` (no trailing period), `author` (`Karunakaran, A.` is bolded automatically), `year`, `venue`, optional `volume`/`issue`/`pages`, `doi` (bare), optional `pdf` (filename in `files/papers/`), optional `equal: true`, `type` (`Journal Article` | `Book Chapter` | `Working Paper`), `categories`, `date` (`YYYY-MM-DD`, controls order within a year), and optional `note` (a one-line takeaway shown under the entry).
- Copy: academic pages in first person, the speaking page in third person. Avoid em dashes. Never invent clients, quotes, statistics, or links.
- Images: always set `width`/`height` to the file's real pixel size.

## How to add content

- **Paper:** `python scripts/add_paper.py --title … --authors … --year … --venue … --doi … [--pdf path] [--equal] [--type "Book Chapter"]`, or edit `papers.yml` by hand. Then `python scripts/build_site.py`.
- **Syllabus:** put the PDF in `files/syllabi/` and add a chip link on the course row in `about.html#teaching`.
- **CV:** overwrite `files/cv/cv.pdf`.
- **News:** add an item at the top of the list in `news.html`, and mirror the newest three in `index.html` → Recent news.
- **Talk video, appearance, client logo, writing:** see the recipes in the `academic-speaker-site` skill (`references/maintenance.md`).
- **Nav or footer change:** edit `partials/`, then `python scripts/build_site.py`.

## Build / verify

```bash
pip install pyyaml                         # once
python scripts/build_site.py               # update pages in place
python scripts/build_site.py --out _site   # full public build, same as CI
python scripts/check_site.py _site         # must report 0 errors
python -m http.server 8000 --directory _site   # preview at http://localhost:8000
```

Commit the updated `.html` files together with the `papers.yml` or partial changes, so the repo and the live site match. Deploy is automatic on push to `main`.

## Speaker reel, one-sheet, photos (organizer kit)

- **Reel:** `files/misc/arvind-karunakaran-speaker-reel.mp4` (about 2 min) and `-60s.mp4` (1 min), poster `images/speaking/reel-poster.jpg`. Raw talk recordings live in `reel-source/`, which is git-ignored and must never be published. The cut is defined in `scripts/reel/edl.json` (clip times, cards, overlays); cards and overlays are generated by `scripts/reel/cards.py` and rendered by `scripts/reel/render_cards.js` (needs `puppeteer-core` and `@sparticuz/chromium`). Build in steps: `build_reel.py segments …` (repeat until done), then `build_reel.py finalize …`. Card text must match `speaking.html`. The opening music is original and synthesized by `scripts/reel/music.py`. The reel uses only the Stanford HAI talk and the New York Fed panel; the full brief for re-cutting it is `scripts/reel/AGENT.md`.
- **One-sheet:** source `scripts/one-sheet/one-sheet.html`, render with `scripts/one-sheet/render.js` to `files/misc/arvind-karunakaran-speaker-one-sheet.pdf` (US Letter, one page; the script fails if the content overflows).
- **Photos:** `files/misc/arvind-karunakaran-photos.zip` holds the headshots and event photos from `images/` at their original sizes. Rebuild it when those photos change.
- After signing with a bureau, point the Enquire button and the one-sheet contact line at the bureau contact.
