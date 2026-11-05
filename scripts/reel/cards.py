#!/usr/bin/env python3
"""Writes the reel's title cards and overlays as 1920x1080 HTML files, in the site's type and colors.

    python scripts/reel/cards.py <cards_dir>
    NODE_PATH=... node scripts/reel/render_cards.js <cards_dir>     # -> PNGs

Every fact on a card must match speaking.html (talk titles, clients, numbers, press). Never add
a client, quote, or statistic that is not on the site.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
FONTS = (ROOT / "fonts").as_uri()
LOGOS = (ROOT / "images" / "logos").as_uri()

BASE = f"""
@font-face {{ font-family: Manrope; src: url("{FONTS}/manrope-latin-wght-normal.woff2") format("woff2"); font-weight: 200 800; }}
@font-face {{ font-family: Inter; src: url("{FONTS}/inter-latin-wght-normal.woff2") format("woff2"); font-weight: 100 900; }}
@font-face {{ font-family: "IBM Plex Mono"; src: url("{FONTS}/ibm-plex-mono-latin-500-normal.woff2") format("woff2"); font-weight: 500; }}
:root {{ --paper:#FBFAF7; --paper-2:#F3F1EC; --ink:#15171B; --ink-2:#444951; --ink-3:#676C74; --rule:#E2DED6;
  --accent:#8C1515; --night:#14171C; --night-2:#1C2128; --on-night:#F4F2EE; --on-night-2:#B3B9C2;
  --accent-on-night:#F29C91; --rule-night:#2C323A; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 1920px; height: 1080px; overflow: hidden; }}
body {{ font-family: Inter, sans-serif; -webkit-font-smoothing: antialiased; }}
.card {{ width: 1920px; height: 1080px; padding: 0 160px; display: flex; flex-direction: column; justify-content: center; }}
.night {{ background: var(--night); color: var(--on-night); }}
.paper {{ background: var(--paper); color: var(--ink); }}
.eyebrow {{ display: flex; align-items: center; gap: 18px; font-family: "IBM Plex Mono"; font-weight: 500; font-size: 26px;
  letter-spacing: .14em; text-transform: uppercase; color: var(--accent); }}
.eyebrow::before {{ content: ""; width: 13px; height: 13px; border-radius: 50%; background: currentColor; flex: none; }}
.night .eyebrow {{ color: var(--accent-on-night); }}
.display {{ font-family: Manrope; font-weight: 300; font-size: 128px; line-height: 1.04; letter-spacing: -0.045em; }}
.display strong {{ font-weight: 700; }}
.hl {{ color: var(--accent-on-night); }}
.mono {{ font-family: "IBM Plex Mono"; font-weight: 500; text-transform: uppercase; letter-spacing: .1em; }}
"""


def page(body, css="", transparent=False):
    bg = "html, body { background: transparent; }" if transparent else ""
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{BASE}{bg}{css}</style></head><body>{body}</body></html>"


CARDS = {}

CARDS["card-title.html"] = page("""
<div class="card night">
  <p class="eyebrow">Keynotes · Executive sessions · Workshops</p>
  <h1 class="display" style="margin-top:46px">An <span style="white-space:nowrap">evidence-based</span> voice<br>on <strong>enterprise AI</strong>.</h1>
  <p class="mono" style="margin-top:64px;font-size:26px;color:var(--on-night-2)">Arvind Karunakaran · Stanford University</p>
</div>""", css=".display { font-size: 136px; }")

CARDS["card-stat.html"] = page("""
<div class="card night">
  <p class="eyebrow">From the field</p>
  <h2 class="h">Same AI tool. Two <span style="white-space:nowrap">near-identical</span> teams.<br><span class="hl">Very different adoption.</span></h2>
  <div class="stats">
    <div class="stat"><b>58<sup>%</sup></b><span>more use of the same AI tool</span></div>
    <div class="stat"><b>70<sup>%</sup></b><span>more experimentation with it</span></div>
  </div>
  <p class="mono src">Field study inside a law firm · Stanford HAI, 2026</p>
</div>""", css="""
.h { margin-top: 40px; font-family: Manrope; font-weight: 400; font-size: 76px; line-height: 1.08; letter-spacing: -0.035em; }
.stats { display: flex; gap: 140px; margin-top: 70px; }
.stat { padding-top: 26px; border-top: 2px solid var(--rule-night); min-width: 520px; }
.stat b { display: block; font-family: Manrope; font-weight: 300; font-size: 200px; line-height: .9; letter-spacing: -0.06em; }
.stat sup { font-size: .42em; font-weight: 400; vertical-align: .95em; margin-left: .04em; color: var(--accent-on-night); }
.stat span { display: block; margin-top: 18px; font-size: 32px; color: var(--on-night-2); }
.src { margin-top: 64px; font-size: 22px; color: var(--on-night-2); }
""")

LOGO_ROW = [
    ("mckinsey.svg", ""), ("bcg.svg", "sq"), ("accenture.svg", ""), ("deloitte.svg", ""), ("pwc.svg", "tall"),
    (None, "Walmart"), ("pepsico.svg", ""), (None, "Nike"), ("unilever.svg", "sq"),
    ("barclays.svg", ""), ("schwab.svg", "sq"), ("novonordisk.svg", "sq"),
]
logos = "".join(
    f'<span class="logo-text">{cls}</span>' if f is None else f'<img class="{cls}" src="{LOGOS}/{f}" alt="">'
    for f, cls in LOGO_ROW)
CARDS["card-clients.html"] = page(f"""
<div class="card paper">
  <p class="eyebrow">Executive sessions for leaders at</p>
  <div class="logos">{logos}</div>
</div>""", css="""
.logos { margin-top: 90px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 84px 70px; align-items: center; justify-items: start; }
.logos img { height: 64px; width: auto; max-width: 300px; object-fit: contain; filter: grayscale(1) brightness(.62) contrast(1.15); opacity: .82; mix-blend-mode: multiply; }
.logos img.sq { height: 104px; } .logos img.tall { height: 84px; }
.logo-text { font-family: Manrope; font-weight: 800; font-size: 50px; letter-spacing: .04em; text-transform: uppercase; color: var(--ink-3); }
""")

TALKS = ["Same Models, Different Results", "Escaping Pilot Purgatory", "Stop Selling AI as a Productivity Tool",
         "What Is AI Really Worth?", "Agentic AI in the Enterprise", "The Organization Is the Bottleneck"]
talks = "".join(f'<li><span class="n">{i:02d}</span>{t}</li>' for i, t in enumerate(TALKS, 1))
CARDS["card-talks.html"] = page(f"""
<div class="card night">
  <p class="eyebrow">Signature framework</p>
  <h2 class="flag">The Workflow Redesign Playbook</h2>
  <p class="sub">Redesigning work around AI with the people who do it</p>
  <p class="eyebrow" style="margin-top:84px">Signature talks</p>
  <ol class="talks">{talks}</ol>
</div>""", css="""
.flag { margin-top: 30px; font-family: Manrope; font-weight: 600; font-size: 92px; line-height: 1.05; letter-spacing: -0.035em; }
.sub { margin-top: 18px; font-family: Manrope; font-weight: 400; font-size: 40px; color: var(--on-night-2); }
.talks { list-style: none; margin-top: 34px; display: grid; grid-template-columns: 1fr 1fr; gap: 0 90px; }
.talks li { display: flex; align-items: baseline; gap: 28px; padding: 22px 0; border-top: 2px solid var(--rule-night);
  font-family: Manrope; font-weight: 500; font-size: 40px; letter-spacing: -0.02em; }
.talks .n { font-weight: 300; color: var(--accent-on-night); font-size: 40px; width: 52px; flex: none; }
""")

CARDS["card-creds.html"] = page("""
<div class="card night">
  <p class="eyebrow">Stanford University</p>
  <ul class="creds">
    <li>Management Science &amp; Engineering</li>
    <li>Faculty affiliate, Stanford HAI</li>
    <li>Thinkers50 Radar</li>
  </ul>
  <p class="press-l mono">Research in Harvard Business Review · Covered by</p>
  <p class="press">The New York Times · The Wall Street Journal · The Washington Post · Financial Times · MSNBC</p>
</div>""", css="""
.creds { list-style: none; margin-top: 40px; }
.creds li { font-family: Manrope; font-weight: 300; font-size: 104px; line-height: 1.12; letter-spacing: -0.04em; }
.creds li:last-child { font-weight: 700; }
.press-l { margin-top: 80px; font-size: 24px; color: var(--on-night-2); }
.press { margin-top: 18px; font-family: Manrope; font-weight: 700; font-size: 35px; letter-spacing: -0.01em; color: var(--on-night); }
""")

CARDS["card-end.html"] = page("""
<div class="card night">
  <p class="eyebrow">Book a keynote, executive session, or workshop</p>
  <h1 class="name">Arvind Karunakaran</h1>
  <p class="role">Stanford University · Management Science &amp; Engineering</p>
  <p class="url">arvindkarunakaran.com/speaking.html</p>
  <p class="mono email">arvindka@stanford.edu</p>
</div>""", css="""
.name { margin-top: 40px; font-family: Manrope; font-weight: 600; font-size: 140px; line-height: 1; letter-spacing: -0.045em; }
.role { margin-top: 28px; font-size: 38px; color: var(--on-night-2); }
.url { margin-top: 86px; font-family: Manrope; font-weight: 600; font-size: 52px; color: var(--accent-on-night); letter-spacing: -0.015em; }
.email { margin-top: 22px; font-size: 26px; color: var(--on-night-2); }
""")

OVERLAY_CSS = """
.wrap { position: absolute; inset: 0; }
.scrim { position: absolute; left: 0; right: 0; bottom: 0; height: 420px; background: linear-gradient(180deg, rgba(10,12,15,0), rgba(10,12,15,.78)); }
.lower { position: absolute; left: 110px; bottom: 96px; color: #fff; }
.lower .nm { font-family: Manrope; font-weight: 600; font-size: 64px; letter-spacing: -0.03em; line-height: 1; }
.lower .rl { margin-top: 16px; font-size: 30px; color: rgba(244,242,238,.86); }
.tag { position: absolute; left: 80px; top: 72px; display: inline-flex; align-items: center; gap: 16px; padding: 16px 26px;
  background: rgba(20,23,28,.78); border-radius: 10px; color: var(--on-night); font-family: "IBM Plex Mono"; font-weight: 500;
  font-size: 24px; letter-spacing: .1em; text-transform: uppercase; }
.tag::before { content: ""; width: 12px; height: 12px; border-radius: 50%; background: var(--accent-on-night); flex: none; }
"""

CARDS["overlay-lower.html"] = page("""
<div class="wrap"><div class="scrim"></div>
  <div class="lower"><div class="nm">Arvind Karunakaran</div><div class="rl">Stanford University · Management Science &amp; Engineering</div></div>
</div>""", css=OVERLAY_CSS, transparent=True)

VENUES = {
    "iia": "Imagination in Action AI Summit at Google · 2026",
    "wharton": "Wharton · Business &amp; Generative AI Workshop · 2024",
    "nyfed": "Federal Reserve Bank of New York · 2026",
    "notredame": "Notre Dame–IBM Technology Ethics Lab",
    "hai": "Stanford HAI",
    "podcast": "Stanford Engineering · The Future of Everything",
    "online": "Stanford Online",
}
for key, label in VENUES.items():
    CARDS[f"overlay-venue-{key}.html"] = page(f'<div class="wrap"><div class="tag">{label}</div></div>', css=OVERLAY_CSS, transparent=True)


def main(out):
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for name, html in CARDS.items():
        (out / name).write_text(html, encoding="utf-8")
    print(f"wrote {len(CARDS)} files to {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "cards")
