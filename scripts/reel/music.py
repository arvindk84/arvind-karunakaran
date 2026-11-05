#!/usr/bin/env python3
"""Original background music for the reel opening, synthesized from scratch with numpy (no samples, no downloads).

    python scripts/reel/music.py scripts/reel/edl.json <work>

For every cut in the edl that has a "music" entry, writes <work>/<music.wav> (48 kHz stereo, 16-bit): a calm,
four-chord loop at 96 BPM (soft pad, piano-like arpeggio, sub bass, a subtle pulse, gentle reverb). It fades in
over 0.5 s, plays under the opening cards, and fades out over 3 s as the first speech clip starts, so it sits
more than 24 dB under the voice by the first word. finalize mixes it under the cut before the loudness pass.

Music keys in a cut:  "music": {"wav": "music-main.wav", "lufs": -20}
The opening length is the time from the start of the cut to the first "clip" segment. The chord loop is
vi-IV-I-V in D major (Bm, G, D, A); the loop is phased so the bar under the fade-out is the tonic (D).
"""
import json
import pathlib
import subprocess
import sys
import wave

import numpy as np

SR = 48000
BPM = 96.0
BEAT = 60.0 / BPM
BAR = 4 * BEAT
LOOP = ["Bm", "G", "D", "A"]
# MIDI notes: bass (sub), pad voicing, arpeggio tones (low to high)
CHORDS = {
    "D": (38, [50, 57, 64, 66, 69], [62, 66, 69, 74, 76, 78]),
    "A": (33, [52, 57, 61, 64, 71], [61, 64, 69, 71, 73, 76]),
    "Bm": (35, [54, 59, 62, 66, 69], [59, 62, 66, 69, 71, 74]),
    "G": (31, [55, 59, 62, 66, 69], [59, 62, 66, 67, 71, 74]),
}
ARP = [0, 2, 4, 3, 5, 3, 4, 2]          # eighth-note pattern over the arpeggio tones
FADE_IN = 0.5
FADE_LEAD = 2.4                          # fade-out starts this long before the first speech clip
FADE_TAIL = 0.6                          # and is silent this long after it starts


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def adsr(n, a, r, sustain_len):
    """Attack (s), hold for sustain_len (s), then release (s); n samples total."""
    t = np.arange(n) / SR
    env = np.clip(t / max(a, 1e-3), 0, 1)
    rel = np.clip(1 - (t - sustain_len) / max(r, 1e-3), 0, 1)
    env = np.minimum(env, np.where(t > sustain_len, rel, 1.0))
    return env * env * (3 - 2 * env)     # smoothstep for click-free edges


def add(buf, start, sig):
    i = int(round(start * SR))
    if i < 0:
        sig, i = sig[-i:], 0
    if i >= buf.shape[0]:
        return
    j = min(buf.shape[0], i + sig.shape[0])
    buf[i:j] += sig[: j - i]


def pad_note(f, length, rng):
    """Warm, slowly moving pad: three detuned soft-saw voices, harmonics rolled off above ~3 kHz."""
    n = int(length * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    nh = int(min(12, 3200 // f))
    tilt = 0.42 + 0.12 * np.sin(2 * np.pi * 0.07 * t + rng.uniform(0, 6.28))   # slow filter movement
    for cents, pan in ((-7, 0.25), (0, 0.5), (7, 0.75)):
        fv = f * 2 ** (cents / 1200)
        v = np.zeros(n)
        for h in range(1, nh + 1):
            v += np.exp(-(h - 1) * tilt) / h ** 1.2 * np.sin(2 * np.pi * h * fv * t + rng.uniform(0, 6.28))
        out[:, 0] += v * np.sqrt(1 - pan)
        out[:, 1] += v * np.sqrt(pan)
    return out / 3


def piano_note(f, vel, rng):
    """Piano-like tone: slightly inharmonic partials, faster decay for higher partials, soft attack."""
    length = 1.8
    n = int(length * SR)
    t = np.arange(n) / SR
    v = np.zeros(n)
    for h in range(1, 11):
        fh = h * f * np.sqrt(1 + 0.00025 * h * h)
        if fh > 9000:
            break
        tau = 1.3 / (1 + 0.55 * (h - 1))
        v += (1 / h ** 1.05) * np.exp(-t / tau) * np.sin(2 * np.pi * fh * t + rng.uniform(0, 6.28))
    att = np.clip(t / 0.006, 0, 1)
    rel = np.clip((length - t) / 0.25, 0, 1)
    return vel * v * att * rel


def sub_note(f, length):
    n = int(length * SR)
    t = np.arange(n) / SR
    v = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(4 * np.pi * f * t) + 0.06 * np.sin(6 * np.pi * f * t)
    return v * adsr(n, 0.03, 0.35, length - 0.4) * np.exp(-t / 1.6)


def kick(length=0.45):
    n = int(length * SR)
    t = np.arange(n) / SR
    f = 46 + 50 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / 0.11) * np.clip(t / 0.002, 0, 1)


def fft_filter(x, fn):
    """Zero-phase filtering in the frequency domain; fn(freqs) -> gain."""
    n = x.shape[0]
    X = np.fft.rfft(x, axis=0)
    g = fn(np.fft.rfftfreq(n, 1 / SR))
    return np.fft.irfft(X * g[:, None], n=n, axis=0)


def reverb_ir(rng, t60=2.2, length=2.6, predelay=0.022):
    n = int(length * SR)
    noise = rng.standard_normal((n, 2))
    noise = fft_filter(noise, lambda f: 1 / np.sqrt(1 + (f / 4200) ** 4))
    t = np.arange(n) / SR
    ir = noise * np.exp(-6.91 * t / t60)[:, None]
    ir = np.concatenate([np.zeros((int(predelay * SR), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum(axis=0, keepdims=True))


def convolve(x, ir):
    n = x.shape[0] + ir.shape[0] - 1
    m = 1 << int(np.ceil(np.log2(n)))
    Y = np.fft.rfft(x, m, axis=0) * np.fft.rfft(ir, m, axis=0)
    return np.fft.irfft(Y, m, axis=0)[: x.shape[0]]


def compose(t0, seed=7):
    """Music for an opening whose first speech clip starts at t0 seconds."""
    rng = np.random.default_rng(seed)
    final_bar = int(round((t0 - FADE_LEAD) / BAR))           # the bar under the fade-out: make it the tonic
    phase = (LOOP.index("D") - final_bar) % 4
    total = t0 + FADE_TAIL + 0.1
    n = int(total * SR) + SR * 4
    pad, arp, sub, kik = (np.zeros((n, 2)) for _ in range(4))
    for b in range(final_bar + 1):
        name = LOOP[(b + phase) % 4]
        bass, voicing, tones = CHORDS[name]
        start = b * BAR
        last = b == final_bar
        hold = BAR * (1.6 if last else 1.0)
        for m in voicing:
            note = pad_note(hz(m), hold + 1.4, rng)
            note *= adsr(note.shape[0], 0.9 if b else 0.4, 1.3, hold)[:, None]
            add(pad, start - (0.12 if b else 0), note)
        # arpeggio: eighth notes; on the final bar only the first two notes, left to ring
        steps = ARP[:2] if last else ARP
        for k, idx in enumerate(steps):
            vel = (0.95 if k == 0 else 0.78 if k % 2 == 0 else 0.66) * rng.uniform(0.9, 1.0)
            jitter = rng.uniform(-0.006, 0.006)
            pan = 0.5 + 0.18 * np.sin(k * 1.3 + b)
            note = piano_note(hz(tones[idx]), vel, rng)
            add(arp, start + k * BEAT / 2 + jitter, np.stack([note * np.sqrt(1 - pan), note * np.sqrt(pan)], 1))
        if b >= 1:   # sub bass and pulse enter after the first bar
            for beat in (0, 2):
                if last and beat == 2:
                    continue
                s = sub_note(hz(bass), BEAT * 2 + 0.3)
                add(sub, start + beat * BEAT, np.stack([s, s], 1))
                k_ = kick()
                add(kik, start + beat * BEAT, np.stack([k_, k_], 1))
    # subtle pulse: the pad ducks a little on every beat (sidechain feel)
    t = np.arange(n) / SR
    ph = (t % BEAT) / BEAT
    duck = 1 - 0.22 * np.exp(-ph * BEAT / 0.16) * (t >= BAR)
    pad *= duck[:, None]
    ir = reverb_ir(rng)
    mix = (0.36 * pad + 0.55 * arp + 0.30 * sub + 0.16 * kik
           + 0.32 * convolve(0.36 * pad + 0.55 * arp, ir) + 0.05 * convolve(0.16 * kik, ir))
    # tone: no rumble, no harsh highs
    mix = fft_filter(mix, lambda f: (1 / np.sqrt(1 + (28 / np.maximum(f, 1)) ** 4)) * (1 / np.sqrt(1 + (f / 10000) ** 4)))
    mix = mix[: int(total * SR)]
    # envelope: 0.5 s fade in; fade out from t0-FADE_LEAD (gentle at first, then quicker) to -28 dB just after
    # t0, when the voice comes in, and to silence by t0+FADE_TAIL
    tt = np.arange(mix.shape[0]) / SR
    g_db = np.interp(tt, [0, t0 - FADE_LEAD, t0 - 1.2, t0 - 0.4, t0 + 0.1, t0 + FADE_TAIL, total],
                     [0, 0, -5, -13, -28, -75, -120])
    g = 10 ** (g_db / 20)
    g *= np.clip(tt / FADE_IN, 0, 1) ** 2
    g[tt >= t0 + FADE_TAIL] = 0
    mix *= g[:, None]
    peak = np.abs(mix).max()
    return mix / peak * 10 ** (-6 / 20), g


def write_wav(path, x):
    x16 = np.clip(x * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(x16.tobytes())


def loudness(path, t1):
    """Integrated loudness (LUFS) of the first t1 seconds (the part before the fade-out)."""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-t", f"{t1:.2f}", "-i", str(path), "-af", "ebur128",
                        "-f", "null", "-"], capture_output=True, text=True)
    tail = p.stderr[p.stderr.rfind("Summary:"):]
    return float(tail.split("I:")[1].split("LUFS")[0])


def seg_dur(e):
    """Same whole-frame (30 fps) durations as build_reel.py."""
    if e["type"] == "card":
        d = float(e["dur"])
    elif e["type"] == "sequence":
        d = sum(float(it["dur"]) for it in e["items"])
    else:
        d = float(e["out"]) - float(e["in"])
    return round(d * 30) / 30


def main(edl_path, work):
    edl = json.loads(pathlib.Path(edl_path).read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in edl["segments"]}
    work = pathlib.Path(work)
    work.mkdir(parents=True, exist_ok=True)
    for cut in edl["cuts"]:
        mu = cut.get("music")
        if not mu:
            continue
        t0 = 0.0
        for sid in cut["segments"]:
            if by_id[sid]["type"] == "clip":
                break
            t0 += seg_dur(by_id[sid])
        mix, _ = compose(t0)
        out = work / mu["wav"]
        write_wav(out, mix)
        lufs = loudness(out, t0 - FADE_LEAD)
        mix *= 10 ** ((float(mu.get("lufs", -20)) - lufs) / 20)
        write_wav(out, mix)
        print(f"wrote {out.name}: {mix.shape[0] / SR:.2f}s, opening {t0:.2f}s, "
              f"{loudness(out, t0 - FADE_LEAD):.1f} LUFS before the fade, peak {20 * np.log10(np.abs(mix).max()):.1f} dBFS")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
