# Builds files/misc/arvind-karunakaran-speaker-reel.en.vtt from a reviewed transcript. Usage: python scripts/reel/captions.py files/misc/arvind-karunakaran-speaker-reel.en.vtt
# Transcript: Whisper large-v3-turbo (run in the browser with transformers.js) run on each speech clip of the published reel (clip times from
# scripts/reel/edl.json), cross-checked against a whisper-small.en pass, then corrected and approved by Arvind (Nov 18, 2026).
# " | " marks a cue break. Each clip's cues share the clip's speech span in proportion to their length.
import sys
CLIPS = [  # (reel start of clip, speech start, speech end within clip, text)
 (25.0,   0.0, 12.32, "What I'm going to talk about is like what happens | after it gets diffused and adopted inside companies, | like how do roles change, how does expertise change, | what happens to the organizational structure aspect."),
 (37.333, 0.0, 10.0,  "That turned out to be really, really critical | than letting the employees alone figure it out. | So here are a couple of key insights that we have found, | which might be helpful for folks in the room."),
 (47.433, 0.0, 12.78, "…that was used, this particular firm called LegalCo, | it's a pseudonym, it's in the Bay Area. | They adopted this tool like way back in 2022, | even before ChatGPT 3.5 was released to the public. | They were an early adopter."),
 (60.233, 0.0, 12.11, "Essentially, it allows people to create these long contracts, | 100-page contracts, faster by combining clauses. | And what we found was when we were studying the firm, | analyzing the logs, like doing a lot of other…"),
 (72.367, 0.0, 10.31, "But I'm worried, like, in the future, | how would management deploy this tool in a manner | that my own role would become weaker, right? | It would be consolidated into a shared service of sorts."),
 (82.7,   0.0, 10.4,  "But even more importantly, what more you could do? | What more complex, higher-order tasks potentially you could do, | given the opening created by AI, | given the excess capacity created?"),
 (93.3,   0.0, 10.08, "…not for any strategic reasons. | This person thought perhaps this is the best way | to position this technology when introducing it. | And we call it, as researchers, we call it like job enrichment."),
 (103.4,  0.0, 11.84, "Obviously you're going to see issues on AI slop, right? | If you're using the old throughput metrics, in the paralegal case, | if the divisions are still using metrics such as caseload."),
 (115.367,0.0, 9.71,  "That did not change, right? | These divisions just increased their workload, | but did not like really match how they're getting evaluated | accordingly at the end of the year."),
 (125.1,  0.0, 11.92, "The composition of the Center of Excellence: | in our own studies we have seen, if it is very homogenous, | just AI experts and some business unit people, | it's not really effective, even economically."),
]
def two_lines(t):
    if len(t) <= 42: return t
    w = t.split(); best = None
    for i in range(1, len(w)):
        a, b = " ".join(w[:i]), " ".join(w[i:])
        score = max(len(a), len(b)) + (0 if a[-1] in ",.?;:" else 4)
        if best is None or score < best[0]: best = (score, a, b)
    return best[1] + "\n" + best[2]
def ts(x): return f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}"
cues = [(0.5, 24.6, "[Music]")]
for off, a, b, text in CLIPS:
    parts = [p.strip() for p in text.split("|")]
    total = sum(len(p) for p in parts); t = off + a; span = b - a
    for p in parts:
        d = span * len(p) / total; cues.append((t, t + d, p)); t += d
out = ["WEBVTT", "", "NOTE Arvind Karunakaran, speaker reel. Captions drafted with Whisper speech recognition (large-v3-turbo); reviewed by Arvind Karunakaran.", ""]
for i, (a, b, t) in enumerate(cues, 1):
    out += [str(i), f"{ts(a)} --> {ts(b)}", two_lines(t), ""]
open(sys.argv[1], "w", encoding="utf-8").write("\n".join(out))
print(len(cues), "cues; longest line", max(len(l) for c in cues for l in two_lines(c[2]).split("\n")),
      "; max chars/s", round(max(len(c[2]) / (c[1] - c[0]) for c in cues[1:]), 1))
