"""Full-episode transcript with timecodes (faster-whisper large-v3-turbo on CPU, Traditional Chinese / Taiwan).

usage: python transcribe.py "<audio or video file>" [--prompt "頻道名，來賓 XXX，聊 OOO"] [--out "<txt path>"]
default out: <file folder>/<file name>_逐字稿.txt   (one line per segment: [HH:MM:SS - HH:MM:SS] text)
Progress lines ("37% 812s") go to stdout so the caller can watch them.

The audio is transcribed in ~5-minute chunks: feeding a 40+ minute episode in one go makes the feature
extraction run out of memory (numpy ArrayMemoryError). Each cut is moved to the quietest moment within
±15 s of the nominal boundary so it does not split a word; timecodes are shifted back to episode time.
"""
import argparse, os, re, sys, time
import numpy as np
import av

# faster-whisper 1.2.1 passes metadata_errors= to av.open, which PyAV 19 no longer accepts.
_av_open = av.open
def _av_open_compat(*a, **kw):
    kw.pop("metadata_errors", None)
    return _av_open(*a, **kw)
av.open = _av_open_compat
from faster_whisper import decode_audio
import whisper_model
import opencc

SR = 16000
CHUNK = 300   # seconds per transcription pass
SEARCH = 15   # seconds either side of each nominal cut to search for silence


# OpenCC s2twp turns the adverb 只 into the measure word 隻 after some words ("就是只能" -> "就是隻能").
# Put 只 back when 隻 is followed by an adverb-style word and not preceded by a number / demonstrative.
ZHI_FIX = re.compile(r"(?<![一二兩三四五六七八九十幾這那每某哪半單])隻(?=能|是|有|要|好|會|想|剩|在|得|不|差|用|因|看|求|怕|顧|管|靠|需|限|准|許|為|做|聽|知|覺)")


def fix_zhi(text):
    return ZHI_FIX.sub("只", text)


def ts(s):
    s = int(s)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def cut_points(audio):
    """sample indices [0, ..., len(audio)]; each inner cut sits in the quietest 0.5 s window near CHUNK s"""
    n, win, cuts = len(audio), SR // 2, [0]
    while n - cuts[-1] > (CHUNK + SEARCH) * SR:
        lo, hi = cuts[-1] + (CHUNK - SEARCH) * SR, cuts[-1] + (CHUNK + SEARCH) * SR
        k = (hi - lo) // win
        energy = np.square(audio[lo:lo + k * win].reshape(k, win)).mean(axis=1)
        cuts.append(lo + int(energy.argmin()) * win + win // 2)
    cuts.append(n)
    return cuts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--prompt", default="")
    ap.add_argument("--out")
    a = ap.parse_args()
    base = os.path.splitext(a.audio)[0]
    out = a.out or base + "_逐字稿.txt"
    cc = opencc.OpenCC("s2twp")
    model = whisper_model.load()
    prompt = "以下是繁體中文的口語內容逐字稿。" + a.prompt
    audio = decode_audio(a.audio, sampling_rate=SR)
    total, cuts = len(audio) / SR, cut_points(audio)
    print(f"duration {total / 60:.1f} min, {len(cuts) - 1} chunks -> {out}", flush=True)
    t0 = time.time()
    with open(out, "w", encoding="utf-8") as f:
        for st, en in zip(cuts, cuts[1:]):
            off = st / SR
            segments, _ = model.transcribe(audio[st:en], language="zh", vad_filter=True, beam_size=5, initial_prompt=prompt)
            for seg in segments:
                f.write(f"[{ts(off + seg.start)} - {ts(off + seg.end)}] {fix_zhi(cc.convert(seg.text.strip()))}\n"); f.flush()
                print(f"{(off + seg.end) / total * 100:.0f}% {time.time() - t0:.0f}s", flush=True)
    print("DONE", out, flush=True)


if __name__ == "__main__":
    sys.exit(main())
