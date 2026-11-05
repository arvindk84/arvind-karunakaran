#!/usr/bin/env python3
"""Cut the speaker reel from the raw recordings in reel-source/ (never published) using an edit list.

Steps (each fits in a short run; segments are cached, so re-running only rebuilds what changed):
    python scripts/reel/cards.py <work>/cards
    NODE_PATH=... node scripts/reel/render_cards.js <work>/cards
    python scripts/reel/music.py scripts/reel/edl.json <work>             # opening music, one WAV per cut
    python scripts/reel/build_reel.py segments scripts/reel/edl.json <work> [--max N]
    python scripts/reel/build_reel.py finalize scripts/reel/edl.json <work> [--cut N]

Each cut in the edl names its output ("out": "files/misc/....mp4") and the segment ids it uses, so the
main reel and the short version share segments.

Segment keys:
  {"id": "...", "type": "clip", "src": "<file in reel-source>", "in": s, "out": s, "frame": "<FRAMES key>",
   "card": {"png": "card-x.png", "dur": s},          # optional J-cut: card over the clip's first seconds
   "cuts": [{"at": s, "frame": "<FRAMES key>"}],     # optional mid-clip reframing, audio unbroken
   "overlays": [{"png": "overlay-x.png", "at": s, "dur": s}]}
  {"id": "...", "type": "card", "png": "card-x.png", "dur": s}   # silent full-frame card
  {"id": "...", "type": "sequence", "xfade": s, "fade_in": s,     # silent opening: cards and B-roll, crossfaded
   "items": [{"png": "card-x.png", "dur": s},
             {"src": "...", "in": s, "frame": "<FRAMES key>", "dur": s, "overlays": [...]}]}
     Each item's "dur" is the time it owns on screen; crossfades are centered on the boundaries.

Cut keys: "out", "title", "segments", optional "music": {"wav": "<file in work>", "lufs": -20} (mixed under the
cut before the loudness pass), optional "poster": "<path>" with "poster_src": {"src", "at", "frame"} (a clean
frame from the raw footage, no overlays) or "poster_at" (a frame of the finished cut).
"""
import hashlib
import json
import pathlib
import subprocess
import sys
import wave

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "reel-source"
FPS = 30
W, H = 1920, 1080
BUILD = 2   # bump when a change here alters the rendered segments, so cached ones are rebuilt


def qdur(d):
    """Durations are whole frames, so each segment's audio and video end together and joined cuts stay in sync."""
    return round(float(d) * FPS) / FPS

# How each source is framed into 1920x1080. Wharton's 4K upload is a composite: the camera feed is
# the left 1920x1080 tile and the slide is the right tile, so both crops are native resolution.
FRAMES = {
    "full": f"scale={W}:{H}:flags=lanczos",
    "wharton-speaker": f"crop=1920:1080:0:540,scale={W}:{H}:flags=lanczos",
    "wharton-slide": f"crop=1920:1080:1920:540,scale={W}:{H}:flags=lanczos",
    "iia-wide": f"scale={W}:{H}:flags=lanczos",
    # The HAI recording has a room label burned into the bottom-left corner; trim the bottom 44 px
    # (and the sides to keep 16:9) so it never shows. About a 4% scale-up.
    "hai": f"crop=1842:1036:39:0,scale={W}:{H}:flags=lanczos",
}
AFMT = "aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo"
# Each source was recorded at a different level: level every segment, then the whole cut at the end.
SEG_LEVEL = "loudnorm=I=-17:TP=-2:LRA=9,aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo"


def venc(crf):
    # Identical settings for every segment so the segments can be joined without re-encoding.
    return ["-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-profile:v", "high", "-level", "4.1",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2), "-keyint_min", str(FPS * 2),
            "-sc_threshold", "0", "-bf", "2"]


AENC = ["-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]


def run(cmd, text=True):
    p = subprocess.run(cmd, capture_output=True, text=text)
    if p.returncode != 0:
        print(" ".join(map(str, cmd)))
        print((p.stderr if text else p.stderr.decode(errors="replace"))[-3000:])
        raise SystemExit(1)
    return p


def overlay_chain(base_label, overlays, first_input, cards_dir, dur):
    """Timed PNG overlays with alpha fades. A full-frame card with fade_in 0 works as a J-cut."""
    args, parts, cur = [], [], base_label
    for k, ov in enumerate(overlays):
        idx = first_input + k
        args += ["-loop", "1", "-t", f"{dur:.6f}", "-i", str(cards_dir / ov["png"])]
        at, d = float(ov["at"]), float(ov["dur"])
        end = min(at + d, dur - 0.05)
        fi, fo = float(ov.get("fade_in", 0.35)), float(ov.get("fade_out", 0.35))
        chain = ["format=rgba"]
        if fi > 0:
            chain.append(f"fade=t=in:st={at:.2f}:d={fi:.2f}:alpha=1")
        if fo > 0:
            chain.append(f"fade=t=out:st={max(at, end - fo):.2f}:d={fo:.2f}:alpha=1")
        parts.append(f"[{idx}:v]{','.join(chain)}[o{k}]")
        nxt = f"v{k + 1}"
        parts.append(f"[{cur}][o{k}]overlay=0:0:enable='between(t,{at:.2f},{end:.2f})'[{nxt}]")
        cur = nxt
    return args, parts, cur


def reframed_source(e, src, t_in, dur, out):
    """For clips with "cuts": render each framing as its own piece (accurate input seek per piece) and
    join them, so the switch points are exact. (A split/trim/concat graph drifts when audio shares the run.)"""
    cuts = [{"at": 0.0, "frame": e.get("frame", "full")}] + list(e["cuts"])
    pieces = []
    for i, c in enumerate(cuts):
        a = float(c["at"])
        b = float(cuts[i + 1]["at"]) if i + 1 < len(cuts) else dur
        p = out.with_name(f"{out.stem}-piece{i}.mkv")
        run(["ffmpeg", "-hide_banner", "-y", "-ss", f"{t_in + a:.3f}", "-t", f"{b - a:.3f}", "-i", str(src), "-an",
             "-vf", f"{FRAMES[c['frame']]},fps={FPS}:start_time=0,format=yuv420p,setsar=1",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "8", "-r", str(FPS), str(p)])
        pieces.append(p)
    lst = out.with_name(f"{out.stem}-pieces.txt")
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
    joined = out.with_name(f"{out.stem}-reframed.mkv")
    run(["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    return joined


def build_clip(e, out, cards_dir, crf):
    src = SRC_DIR / e["src"]
    t_in, t_out = float(e["in"]), float(e["out"])
    dur = qdur(t_out - t_in)
    overlays = list(e.get("overlays", []))
    if e.get("card"):
        c = e["card"]
        overlays.insert(0, {"png": c["png"], "at": 0, "dur": float(c["dur"]), "fade_in": 0,
                            "fade_out": float(c.get("dissolve", 0.45))})
    # Input 0: video (pre-reframed if the clip has cuts). Input 1: the same span of the source for audio.
    if e.get("cuts"):
        vin = ["-i", str(reframed_source(e, src, t_in, dur, out))]
        vparts = ["[0:v]null[v0]"]
    else:
        # read a little past the out-point so the 25->30 fps conversion has its last frame; -t below trims exactly
        vin = ["-ss", f"{t_in:.3f}", "-t", f"{dur + 1.0:.6f}", "-i", str(src)]
        # start_time=0 keeps the 30 fps grid on the audio's clock (the first source frame can land up to one
        # source frame after the seek point), so every clip is exactly round(dur*30) frames and in sync
        vparts = [f"[0:v]{FRAMES[e.get('frame', 'full')]},fps={FPS}:start_time=0,format=yuv420p,setsar=1[v0]"]
    ain = ["-ss", f"{t_in:.3f}", "-t", f"{dur:.6f}", "-i", str(src)]
    ov_args, ov_parts, last = overlay_chain("v0", overlays, 2, cards_dir, dur)
    af = f"{AFMT},{SEG_LEVEL},afade=t=in:st=0:d=0.06,afade=t=out:st={dur - 0.09:.3f}:d=0.09"
    run(["ffmpeg", "-hide_banner", "-y"] + vin + ain + ov_args +
        ["-filter_complex", ";".join(vparts + ov_parts), "-map", f"[{last}]", "-map", "1:a", "-af", af,
         "-t", f"{dur:.6f}"] + venc(crf) + AENC + [str(out)])


def build_card(e, out, cards_dir, crf):
    dur = qdur(e["dur"])
    fade = float(e.get("fade", 0.4))
    vf = (f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1,"
          f"fade=t=in:st=0:d={fade},fade=t=out:st={dur - fade:.3f}:d={fade}[v]")
    run(["ffmpeg", "-hide_banner", "-y", "-loop", "1", "-t", f"{dur:.6f}", "-framerate", str(FPS),
         "-i", str(cards_dir / e["png"]), "-f", "lavfi", "-t", f"{dur:.6f}", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", f"{vf};[1:a]{AFMT}[a]", "-map", "[v]", "-map", "[a]", "-t", f"{dur:.6f}"]
        + venc(crf) + AENC + [str(out)])


def build_sequence(e, out, cards_dir, crf):
    """Silent opening: full-frame cards and B-roll shots joined with crossfades (video only, so no audio drift),
    then a silent track. Music is mixed in at finalize."""
    xf = float(e.get("xfade", 0.4))
    items = e["items"]
    spans = [float(it["dur"]) for it in items]
    total = qdur(sum(spans))
    starts = [sum(spans[:i]) for i in range(len(spans))]
    pieces = []
    for i, it in enumerate(items):
        s0, s1 = starts[i], starts[i] + spans[i]
        a = max(0.0, s0 - xf / 2)
        b = min(total, s1 + xf / 2)
        d = b - a
        p = out.with_name(f"{out.stem}-item{i}.mkv")
        if it.get("png"):
            vin = ["-loop", "1", "-t", f"{d:.3f}", "-framerate", str(FPS), "-i", str(cards_dir / it["png"])]
            base = f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1[v0]"
        else:
            src = SRC_DIR / it["src"]
            vin = ["-ss", f"{float(it['in']) - (s0 - a):.3f}", "-t", f"{d + 1.0:.3f}", "-i", str(src)]
            base = f"[0:v]{FRAMES[it.get('frame', 'full')]},fps={FPS}:start_time=0,format=yuv420p,setsar=1[v0]"
        ovs = [dict(o, at=float(o["at"]) + (s0 - a)) for o in it.get("overlays", [])]
        ov_args, ov_parts, last = overlay_chain("v0", ovs, 1, cards_dir, d)
        run(["ffmpeg", "-hide_banner", "-y"] + vin + ov_args +
            ["-filter_complex", ";".join([base] + ov_parts), "-map", f"[{last}]", "-an", "-t", f"{d:.3f}",
             "-c:v", "libx264", "-preset", "ultrafast", "-crf", "8", "-r", str(FPS), str(p)])
        pieces.append(p)
    args, parts, cur = [], [], "0:v"
    for i, p in enumerate(pieces):
        args += ["-i", str(p)]
    for i in range(1, len(pieces)):
        nxt = f"x{i}"
        parts.append(f"[{cur}][{i}:v]xfade=transition=fade:duration={xf:.3f}:offset={starts[i] - xf / 2:.3f}[{nxt}]")
        cur = nxt
    fi = float(e.get("fade_in", 0.5))
    parts.append(f"[{cur}]fade=t=in:st=0:d={fi:.2f},format=yuv420p,setsar=1[v]")
    n = len(pieces)
    run(["ffmpeg", "-hide_banner", "-y"] + args +
        ["-f", "lavfi", "-t", f"{total:.6f}", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", ";".join(parts) + f";[{n}:a]{AFMT}[a]", "-map", "[v]", "-map", "[a]", "-t", f"{total:.6f}"]
        + venc(crf) + AENC + [str(out)])


def seg_key(e, cards_dir, crf):
    h = hashlib.sha1(json.dumps(e, sort_keys=True).encode())
    h.update(json.dumps(FRAMES, sort_keys=True).encode())
    h.update(f"{crf}|{SEG_LEVEL}|{BUILD}".encode())
    pngs = [e.get("png"), (e.get("card") or {}).get("png")] + [o["png"] for o in e.get("overlays", [])]
    for it in e.get("items", []):
        pngs += [it.get("png")] + [o["png"] for o in it.get("overlays", [])]
    for png in pngs:
        if png:
            h.update((cards_dir / png).read_bytes())
    return h.hexdigest()[:16]


def duration(e):
    if e["type"] == "card":
        return qdur(e["dur"])
    if e["type"] == "sequence":
        return qdur(sum(float(it["dur"]) for it in e["items"]))
    return qdur(float(e["out"]) - float(e["in"]))


def segments(edl, work, max_new):
    cards_dir, seg_dir = work / "cards", work / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    crf = edl.get("crf", 22)
    built = 0
    for e in edl["segments"]:
        key = seg_key(e, cards_dir, crf)
        out = seg_dir / f"{e['id']}-{key}.mkv"
        if out.exists():
            continue
        if built >= max_new:
            print("  (more segments to build; run again)")
            return False
        {"clip": build_clip, "card": build_card, "sequence": build_sequence}[e["type"]](e, out, cards_dir, crf)
        built += 1
        print(f"  built {e['id']:12s} {duration(e):5.2f}s")
    print("  all segments built")
    return True


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        if w.getframerate() != 48000 or w.getnchannels() != 2 or w.getsampwidth() != 2:
            raise SystemExit(f"{path}: expected 48 kHz stereo 16-bit")
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").reshape(-1, 2).astype(np.float32) / 32768


def write_wav(path, x):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(48000)
        w.writeframes(np.clip(np.round(x * 32767), -32768, 32767).astype("<i2").tobytes())


def mix_music(joined, music_wav, out_wav):
    """Sum the music under the cut's own audio (sample-exact, outside any filter graph)."""
    raw = run(["ffmpeg", "-hide_banner", "-v", "error", "-i", str(joined), "-vn", "-ac", "2", "-ar", "48000",
               "-f", "s16le", "-"], text=False).stdout
    a = np.frombuffer(raw, dtype="<i2").reshape(-1, 2).astype(np.float32) / 32768
    m = read_wav(music_wav)
    n = min(a.shape[0], m.shape[0])
    a[:n] += m[:n]
    write_wav(out_wav, a)


def finalize(edl, work, only=None):
    cards_dir, seg_dir = work / "cards", work / "segments"
    crf = edl.get("crf", 22)
    by_id = {e["id"]: e for e in edl["segments"]}
    for ci, cut in enumerate(edl["cuts"]):
        if only is not None and ci != only:
            continue
        files, total = [], 0.0
        for sid in cut["segments"]:
            e = by_id[sid]
            f = seg_dir / f"{sid}-{seg_key(e, cards_dir, crf)}.mkv"
            if not f.exists():
                raise SystemExit(f"segment {sid} not built yet; run the segments step")
            files.append(f)
            total += duration(e)
        name = pathlib.Path(cut["out"]).stem
        lst = work / f"{name}.txt"
        lst.write_text("".join(f"file '{f.as_posix()}'\n" for f in files), encoding="utf-8")
        joined = work / f"{name}-joined.mkv"
        run(["ffmpeg", "-hide_banner", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
        audio_in = ["-i", str(joined)]
        if cut.get("music"):
            mixed = work / f"{name}-mixed.wav"
            mix_music(joined, work / cut["music"]["wav"], mixed)
            audio_in = ["-i", str(mixed)]
        # Two-pass EBU R128 loudness on the whole cut: -16 LUFS, true peak -1.5 dB. Video is copied.
        p = run(["ffmpeg", "-hide_banner"] + audio_in + ["-vn", "-af",
                 "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
        t = p.stderr
        m = json.loads(t[t.rfind("{"):t.rfind("}") + 1])
        ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        out = ROOT / cut["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-hide_banner", "-y", "-i", str(joined)] + audio_in + ["-map", "0:v", "-map", "1:a", "-c:v", "copy",
             "-af", f"{ln},aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo", "-c:a", "aac", "-b:a", "160k",
             "-shortest", "-movflags", "+faststart",
             "-metadata", f"title={cut.get('title', 'Arvind Karunakaran · Speaker reel')}", str(out)])
        if cut.get("poster"):
            ps = cut.get("poster_src")
            if ps:   # a clean frame from the raw footage: no cards, tags, or lower thirds
                run(["ffmpeg", "-hide_banner", "-y", "-ss", f"{float(ps['at']):.3f}", "-i", str(SRC_DIR / ps["src"]),
                     "-frames:v", "1", "-vf", f"{FRAMES[ps.get('frame', 'full')]},scale=1600:900:flags=lanczos",
                     "-q:v", "2", str(ROOT / cut["poster"])])
            else:
                run(["ffmpeg", "-hide_banner", "-y", "-ss", f"{float(cut.get('poster_at', 1.0)):.2f}", "-i", str(out),
                     "-frames:v", "1", "-vf", "scale=1600:900:flags=lanczos", "-q:v", "3", str(ROOT / cut["poster"])])
        print(f"wrote {out.relative_to(ROOT)}  {out.stat().st_size / 1e6:.1f} MB  {total:.1f}s")


if __name__ == "__main__":
    step, edl_path, work = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
    edl = json.loads(pathlib.Path(edl_path).read_text(encoding="utf-8"))
    if step == "segments":
        n = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 99
        segments(edl, work, n)
    elif step == "finalize":
        finalize(edl, work, int(sys.argv[sys.argv.index("--cut") + 1]) if "--cut" in sys.argv else None)
    else:
        raise SystemExit("step must be 'segments' or 'finalize'")
