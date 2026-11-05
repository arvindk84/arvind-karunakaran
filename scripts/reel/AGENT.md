# Speaker reel agent: brief

Instructions for an agent that cuts Arvind Karunakaran's speaker reel. Reuse this file for future re-cuts.

## Goal

Two cuts, both rebuilt from scratch:

- `files/misc/arvind-karunakaran-speaker-reel.mp4`: main reel, 2:00 to 2:30.
- `files/misc/arvind-karunakaran-speaker-reel-60s.mp4`: short version, about 60 s.
- `images/speaking/reel-poster.jpg`: 1600x900 poster, a clean frame of Arvind on stage with no overlays.

Only two recordings may appear: the **Stanford HAI talk** and the **Federal Reserve Bank of New York panel**. Intercut between them by content.

## Paths (bash paths; Windows equivalents are under `C:\Users\arvindka\academic-website`)

- Repo: `/sessions/keen-loving-ride/mnt/academic-website`. Read `CLAUDE.md` first (section "Speaker reel, one-sheet, photos").
- Raw footage: `reel-source/` (git-ignored). Never copy raw footage into `files/` or `images/`, and never publish it.
  - `05 - Stanford HAI - Instacart Conversation [ZByKqo03krQ].mkv`: 1080p25, 72 min, recorded Sept 23, 2026. Arvind's solo talk runs about 1300 to 2900 s (Alexandr Lenk of Instacart presents before him; joint Q&A from about 2924 s). His slides are visible on the screens behind him. A room label and phone number are burned into the bottom-left corner: always frame this source with `FRAMES["hai"]`, which crops it out.
  - `01 - New York Fed - AI in the Workplace - speaker section [6406544535112].mp4`: 1080p60, 38:51, starts where Arvind first speaks. Multi-camera: a wide shot of the three panelists (moderator Kartik Athreya on the left, Arvind in the center, Roshni Raveendhran of UVA Darden on the right) and close-ups of Arvind. Other people speak too. Use only moments where Arvind is the one speaking.
- Pipeline: `scripts/reel/cards.py` (card and overlay HTML), `scripts/reel/render_cards.js` (HTML to PNG), `scripts/reel/build_reel.py` (`segments` and `finalize` steps, cached), `scripts/reel/edl.json` (edit list; schema in the `build_reel.py` docstring).
- Chromium for rendering: `NODE_PATH=/tmp/shot/node_modules` (puppeteer-core and @sparticuz/chromium are installed).
- Work folder for intermediates: `/sessions/keen-loving-ride/work/reelv3`.
- Pause finder: `python3 /sessions/keen-loving-ride/work/reel/pauses.py <file> <start_s> <dur_s>` prints low-energy gaps (likely sentence boundaries).

## Hard limits

- Each bash call must finish in under about 170 s, and nothing backgrounded survives the call. Build segments in batches (`segments ... --max N`, repeat), then `finalize` in its own call.
- Do not use split/trim/concat in the same ffmpeg graph as the audio (the timing drifts). `build_reel.py` already renders mid-clip reframes as separate pieces.
- Web fetch is disabled for this organization. Use WebSearch only. Never use curl, wget, Python, yt-dlp, or any other tool to fetch anything from the internet, and do not download ML models.
- No em dashes anywhere. No hype words. Every fact on a card must match `speaking.html` or the one-sheet (`scripts/one-sheet/one-sheet.html`). Never invent clients, numbers, quotes, or titles.

## Content: look up what he says, then intercut

1. Find out what Arvind covers in each recording:
   - WebSearch for public descriptions or coverage of both events (the HAI seminar page or HAI news; the NY Fed 2026 Governance & Culture Reform Conference page or recaps).
   - HAI: OCR his slides (tesseract 4.1.1 is installed). Sample a frame every 5 to 10 s across 1300 to 2900 s, crop the screens behind him, and record the slide title or key text over time.
   - Optional weak hint: pocketsphinx keyword spotting (`pip install pocketsphinx --break-system-packages`; the wheel bundles an English model; ffmpeg also has an `asr` filter using `/usr/share/pocketsphinx/model`). Accuracy is poor, so never rely on it alone.
   - NY Fed: use the camera and turn structure (close-ups of Arvind, the pauses between speakers) to find his answers.
2. Pick 7 to 14 s clips, cut only on pauses, never mid-word or mid-sentence where you can avoid it.
3. Alternate HAI and NY Fed, placing clips on related themes next to each other.
4. In your report, list every clip with source file, in and out times, what it is about, how you know, and your confidence. Say plainly what you could not verify.

## Opening with music (main reel about 20 to 25 s; short version about 10 to 12 s)

- Original music, synthesized locally (numpy or scipy; no samples, no downloads). Calm, confident, modern: for example 92 to 100 BPM, a four-chord loop, soft pad, light piano-like arpeggio, sub bass, a subtle pulse, gentle reverb. No harsh highs, no clipping. Fade in about 0.5 s. Music plays only in the opening and fades out over 2 to 3 s as the first speech clip starts; anything left under speech must sit at least 24 dB below the voice.
- The opening outlines his research on AI, drawn from the one-sheet:
  - title card (exists: `card-title.png`);
  - what he studies: "what actually happens inside organizations when they adopt AI, and why the bottleneck is rarely the technology" (from the speaking page bio);
  - **the framework card** (new), recreated from page 5 of `/sessions/keen-loving-ride/mnt/uploads/ArvindKarunakaran_Hackathon_Exercise - Workflow Job Org Redesign and Value.pdf`. Keep the slide's wording exactly: title "A framework for job, workflow, and organizational redesign"; four lenses: BUNDLES "Is the job splittable at all?"; CHAINS "Are the AI-able steps next to each other?"; BOTTLENECKS "Where is the weak link?"; VACANCY CHAINS "Where do the displaced tasks land?". You may add each lens's one-line description and citation exactly as on the slide. Do not paraphrase;
  - the 58% and 70% field finding (exists: `card-stat.png`);
  - client logos (exists: `card-clients.png`);
  - **a one-sheet card** (new): the rendered one-sheet page (`scripts/one-sheet/preview.png`, 1632x2112, or render the PDF) with the label "Speaker one-sheet" and "arvindkarunakaran.com/speaking.html".
- Silent B-roll of Arvind on the HAI stage or the NY Fed stage may sit under the music between cards.
- Card style: use the BASE CSS in `cards.py` (site fonts, night and paper colors, cardinal accent). Keep a card on screen long enough to read (about 3 to 5 s; the framework card about 6 s).

## Rest of the reel

- Intercut HAI and NY Fed clips. Put the name lower third (`overlay-lower.png`) on the first speech clip. Use venue tags on clips (`overlay-venue-hai.png`, `overlay-venue-nyfed.png`; you may change the HAI tag text to "Stanford HAI · 2026").
- Reuse `card-talks.png`, `card-creds.png`, and `card-end.png` as J-cuts or closers where they help.
- Keep integrated loudness at -16 LUFS and each file under 45 MB.

## Verify before reporting

- A frame contact sheet every 3 s for each cut: no burned-in label, cards correct, nothing from other recordings.
- ebur128 loudness for each cut, and a check of the music level and its fade into the first clip.
- Durations and file sizes.

## Scope

- You may change `scripts/reel/*`, the two reel MP4s, and the poster. Do not edit `speaking.html` or any other site page, and do not commit.
