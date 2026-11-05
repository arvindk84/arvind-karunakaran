#!/usr/bin/env python3
"""Cut the speaker reel from the raw recordings in reel-source/ (never published) using an edit list.

Steps (each fits in a short run; segments are cached, so re-running only rebuilds what changed):
    python scripts/reel/cards.py <work>/cards
    NODE_PATH=... node scripts/reel/render_cards.js <work>/cards
    python scripts/reel/build_reel.py segments scripts/reel/edl.json <work> [--max N]
    python scripts/reel/build_reel.py finalize scripts/reel/edl.json <work>

Each cut in the edl names its output ("out": "files/misc/....mp4") and the segment ids it uses, so the
main reel and the short version share segments.

Segment keys:
  {"id": "...", "type": "clip", "src": "<file in reel-source>", "in": s, "out": s, "frame": "<FRAMES key>",
   "card": {"png": "card-x.png", "dur": s},          # optional J-cut: card over the clip's first seconds
   "cuts": [{"at": s, "frame": "<FRAMES key>"}],     # optional mid-clip reframing, audio unbroken
   "overlays": [{"png": "overlay-x.png", "at": s, "dur": s}]}
  {"id": "...", "type": "card", "png": "card-x.png", "dur": s}   # silent full-frame card
"""
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC_DIR = ROOT / "reel-source"
FPS = 30
W, H = 1920, 1080

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


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(" ".join(map(str, cmd)))
        print(p.stderr[-3000:])
        raise SystemExit(1)
    return p


def overlay_chain(base_label, overlays, first_input, cards_dir, dur):
    """Timed PNG overlays with alpha fades. A full-frame card with fade_in 0 works as a J-cut."""
    args, parts, cur = [], [], base_label
    for k, ov in enumerate(overlays):
        idx = first_input + k
        args += ["-loop", "1", "-t", f"{dur:.3f}", "-i", str(cards_dir / ov["png"])]
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
             "-vf", f"{FRAMES[c['frame']]},fps={FPS},format=yuv420p,setsar=1",
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
    dur = t_out - t_in
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
        vin = ["-ss", f"{t_in:.3f}", "-t", f"{dur:.3f}", "-i", str(src)]
        vparts = [f"[0:v]{FRAMES[e.get('frame', 'full')]},fps={FPS},format=yuv420p,setsar=1[v0]"]
    ain = ["-ss", f"{t_in:.3f}", "-t", f"{dur:.3f}", "-i", str(src)]
    ov_args, ov_parts, last = overlay_chain("v0", overlays, 2, cards_dir, dur)
    af = f"{AFMT},{SEG_LEVEL},afade=t=in:st=0:d=0.06,afade=t=out:st={dur - 0.09:.3f}:d=0.09"
    run(["ffmpeg", "-hide_banner", "-y"] + vin + ain + ov_args +
        ["-filter_complex", ";".join(vparts + ov_parts), "-map", f"[{last}]", "-map", "1:a", "-af", af,
         "-t", f"{dur:.3f}"] + venc(crf) + AENC + [str(out)])


def build_card(e, out, cards_dir, crf):
    dur = float(e["dur"])
    fade = float(e.get("fade", 0.4))
    vf = (f"[0:v]scale={W}:{H},fps={FPS},format=yuv420p,setsar=1,"
          f"fade=t=in:st=0:d={fade},fade=t=out:st={dur - fade:.3f}:d={fade}[v]")
    run(["ffmpeg", "-hide_banner", "-y", "-loop", "1", "-t", f"{dur:.3f}", "-framerate", str(FPS),
         "-i", str(cards_dir / e["png"]), "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
         "-filter_complex", f"{vf};[1:a]{AFMT}[a]", "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}"]
        + venc(crf) + AENC + [str(out)])


def seg_key(e, cards_dir, crf):
    h = hashlib.sha1(json.dumps(e, sort_keys=True).encode())
    h.update(json.dumps(FRAMES, sort_keys=True).encode())
    h.update(f"{crf}|{SEG_LEVEL}".encode())
    for png in [e.get("png"), (e.get("card") or {}).get("png")] + [o["png"] for o in e.get("overlays", [])]:
        if png:
            h.update((cards_dir / png).read_bytes())
    return h.hexdigest()[:16]


def duration(e):
    return float(e["dur"]) if e["type"] == "card" else float(e["out"]) - float(e["in"])


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
        (build_clip if e["type"] == "clip" else build_card)(e, out, cards_dir, crf)
        built += 1
        print(f"  built {e['id']:12s} {duration(e):5.2f}s")
    print("  all segments built")
    return True


def finalize(edl, work):
    cards_dir, seg_dir = work / "cards", work / "segments"
    crf = edl.get("crf", 22)
    by_id = {e["id"]: e for e in edl["segments"]}
    for cut in edl["cuts"]:
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
        # Two-pass EBU R128 loudness on the whole cut: -16 LUFS, true peak -1.5 dB. Video is copied.
        p = run(["ffmpeg", "-hide_banner", "-i", str(joined), "-vn", "-af",
                 "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
        t = p.stderr
        m = json.loads(t[t.rfind("{"):t.rfind("}") + 1])
        ln = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
        out = ROOT / cut["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        run(["ffmpeg", "-hide_banner", "-y", "-i", str(joined), "-map", "0:v", "-map", "0:a", "-c:v", "copy",
             "-af", f"{ln},aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", "-metadata", f"title={cut.get('title', 'Arvind Karunakaran · Speaker reel')}", str(out)])
        if cut.get("poster"):
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
        finalize(edl, work)
    else:
        raise SystemExit("step must be 'segments' or 'finalize'")
