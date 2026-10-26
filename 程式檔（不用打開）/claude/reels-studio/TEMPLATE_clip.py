"""Clip script template (illustrated mode: audio-only source, every picture drawn) —
copy to <recording folder>/_reels_work/clipN/clip.py and fill in the 4 marked blocks.
For a speaker who filmed themselves, start from TEMPLATE_face_clip.py instead.

  python clip.py audio    -> check every cut prints OK, else move it into a silence from words.py output
  python clip.py sheet    -> READ sheet_*.png and fix overlaps / empty frames before rendering
  python clip.py render   -> final MP4 + verify
"""
import math, os, sys, random
sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "reels-studio"))
from reels_lib import *            # noqa: F401,F403  (palette, Xf, P, text, shapes, Timeline, Reel, ...)
import props                       # ready-made objects: props.mug, props.sprout, props.balance ... (see its docstring)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "RECORDING_Reels_片段N.mp4")    # <- final file next to the recording

# ---- 1. edit: kept source ranges (recording seconds), every edge inside a silence ----
TL = Timeline(
    keeps=[(100.00, 112.40), (112.90, 130.10)],
    seg_t0=95.0,            # = t0 given to words.py
    end_hold=0.4,           # extra hold after the last word (longer if the last subtitle is a punch card)
)
o = TL.o

# ---- 2. subtitles: (text, SOURCE second, who). who: 'r' main speaker / 'h' second speaker (brand label chip) /
#         any name string = chip with that name. ≤12 chars per line, '|' = new line, 【】 = keyword,
#         leading '!' = punch card. Write what is said; dropping pure fillers is fine. ----
SUBS = [
    ("第一句字幕|【關鍵字】在這裡", 100.05, "r"),
    ("!【金句】", 120.30, "r"),
]

# ---- 3. scenes: fn(c, t, lt, dur). t = global sec, lt = sec since scene start. Sync beats with R.L(name, src). ----
def sc_title(c, t, lt, dur):
    title_card(c, t, lt, ["你上一次覺得", "「活著就很【幸福】」", "是什麼時候？"], "小標語")

def sc_example(c, t, lt, dur):
    paper_bg(c, t); deco(c, t)
    k = eback(prog(lt, 0, 0.45), 1.8)                       # pop in
    with Xf(c, 540, 840, k, 4 * math.sin(t * 2)):            # idle wobble
        props.mug(c, crack=prog(lt, 0.5, 1.0), fill=0.6, leak=0, t=t)
    beat = R.L("example", 120.30)                            # moment a word is spoken
    if lt > beat:
        with Xf(c, 820, 520, eback(prog(lt, beat, 0.35), 2.5), -8): stamp(c, "就是這句", ACC, 80)

# Pexels stock media (STYLE.md §9): files from `pexels.py get ...` land in ./assets
A = os.path.join(HERE, "assets")
def sc_stock_example(c, t, lt, dur):                         # not in SCENES — copy when needed
    video_scene(c, os.path.join(A, "pexels_video_123.mp4"), lt, dur, offset=1.0, grade="warm")
    deco(c, t, 0.6)                                          # illustrations can sit on top of footage

def sc_end(c, t, lt, dur):
    end_card(c, t, lt)                                       # name / CTA / icon from brand.json
    # podcast-style: end_card(c, t, lt, guest="來賓名", ep="EP80")  -> 「EP80｜來賓名」

SCENES = [
    ("title", 0.0, sc_title),
    ("example", 3.0, sc_example),
    ("end", TL.END_START, sc_end),
]
# ---- 4. transitions into each scene: circle / slide / zoom / cut (rotate them, 'cut' for hard hits like 「砰」) ----
TRANS = {"example": "circle", "end": "circle"}

R = Reel(HERE, os.path.abspath(OUT), TL, SUBS, SCENES, TRANS)   # tag=... overrides the top label (default: brand)

if __name__ == "__main__":
    R.cli()
