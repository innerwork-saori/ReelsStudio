"""Cut one clip region out of a recording and get word-level timestamps + a silence map for choosing cut points.

usage: python words.py "<recording: audio or video>" <t0 sec> <t1 sec | end> <clip dir> [--prompt "主題關鍵字"]
writes  <clip dir>/seg.wav        48 kHz stereo audio of [t0, t1]  (SEG_T0 = t0)
        <clip dir>/words.json     [{t0, t1, w}] in SOURCE seconds (= the recording's own clock)
prints  every word, then every silence >= 0.25 s (< -38 dB) inside the range — cut points must sit inside these.
Tip: pad t0/t1 by ~5 s around the clip you picked from the transcript. For a short video used whole: 0 end.
"""
import argparse, json, os
import av, numpy as np, soundfile as sf

# faster-whisper 1.2.1 passes metadata_errors= to av.open, which PyAV 19 no longer accepts.
_av_open = av.open
def _av_open_compat(*a, **kw):
    kw.pop("metadata_errors", None)
    return _av_open(*a, **kw)
av.open = _av_open_compat
from faster_whisper import WhisperModel
import opencc

MODEL = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"


def extract(src, t0, t1, out_wav):
    c = av.open(src); st = c.streams.audio[0]
    res = av.AudioResampler(format="fltp", layout="stereo", rate=48000)
    c.seek(int(max(0, t0 - 2) / st.time_base), stream=st)
    chunks, start = [], None
    for fr in c.decode(st):
        # the resampler's output stream begins at the first frame fed in, even if it only emits samples a frame later
        if start is None: start = float(fr.pts * st.time_base)
        for r in res.resample(fr): chunks.append(r.to_ndarray())
        if fr.pts * st.time_base > t1 + 1: break
    for r in res.resample(None): chunks.append(r.to_ndarray())      # flush what the resampler still holds
    a = np.concatenate(chunks, axis=1)
    off = int((t0 - start) * 48000)
    if off < 0: a = np.concatenate([np.zeros((2, -off), a.dtype), a], axis=1); off = 0   # t0 before the first sample
    a = a[:, off: off + int((t1 - t0) * 48000)]
    sf.write(out_wav, a.T, 48000)


def silences(wav, seg_t0, min_len=0.25, thresh=-38):
    a, sr = sf.read(wav); m = a.mean(1) if a.ndim > 1 else a
    hop = int(.01 * sr)
    db = np.array([20 * np.log10(np.sqrt(np.mean(m[i:i + 2 * hop] ** 2)) + 1e-9) for i in range(0, len(m) - 2 * hop, hop)])
    out, start = [], None
    for i, q in enumerate(db < thresh):
        if q and start is None: start = i
        if not q and start is not None:
            if (i - start) * 0.01 >= min_len: out.append((seg_t0 + start * 0.01, seg_t0 + i * 0.01))
            start = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio"); ap.add_argument("t0", type=float); ap.add_argument("t1"); ap.add_argument("clipdir")
    ap.add_argument("--prompt", default="")
    a = ap.parse_args()
    if a.t1 == "end":
        with av.open(a.audio) as c: a.t1 = c.duration / 1e6
    a.t1 = float(a.t1)
    os.makedirs(a.clipdir, exist_ok=True)
    wav = os.path.join(a.clipdir, "seg.wav")
    extract(a.audio, a.t0, a.t1, wav)
    m = WhisperModel(MODEL, device="cpu", compute_type="int8", cpu_threads=max(2, (os.cpu_count() or 4) - 2))
    cc = opencc.OpenCC("s2twp")
    segs, _ = m.transcribe(wav, language="zh", word_timestamps=True, beam_size=5,
                           initial_prompt="以下是繁體中文的口語內容。" + a.prompt)
    words = [{"t0": round(w.start + a.t0, 2), "t1": round(w.end + a.t0, 2), "w": cc.convert(w.word)} for s in segs for w in s.words]
    json.dump(words, open(os.path.join(a.clipdir, "words.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"SEG_T0 = {a.t0}")
    print(" | ".join(f"{w['t0']:.2f}-{w['t1']:.2f} {w['w'].strip()}" for w in words))
    print("\nsilences (cut points go inside these):")
    for s, e in silences(wav, a.t0): print(f"  {s:.2f}-{e:.2f} ({e - s:.2f}s)")


if __name__ == "__main__":
    main()
