"""Clip script template (text-card mode, 純字卡: no recording at all) —
copy to <material folder>/_reels_work/clipN/clip.py and fill in the 3 marked blocks.
The 口播稿 is not read aloud: its lines become subtitle cards, each held long enough to read (brand.json layout.pace),
over drawn scenes like the illustrated mode. The video is silent; the user adds music in the IG / TikTok app.
Check the channel's brand.json first: layout (title card / end card / subtitle size / pace) and style "free".

  python clip.py sheet    -> prints each card's time, READ sheet_*.png and fix overlaps / empty frames
  python clip.py render   -> final MP4 (silent soundtrack) + verify
"""
import math, os, sys, random
sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "reels-studio"))
from reels_lib import *            # noqa: F401,F403  (palette, Xf, P, text, shapes, text_cards, Reel, ...)
import props                       # ready-made objects: props.mug, props.sprout, props.balance ... (see its docstring)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "TOPIC_Reels_片段1.mp4")      # <- <主題>_Reels_片段N.mp4 in the material folder

# ---- 1. cards, in order: text | (text, hold_sec) | (text, hold_sec, who). Same rules as subtitles: ≤SUB_MAX chars
#         per line, '|' = new line, 【】 = keyword, leading '!' = punch card. hold_sec None = by length.
#         One idea per card; 25-40 s in total is plenty for a silent reel. ----
CARDS = [
    "你是不是也常常|覺得【休息】很有罪惡感？",
    "好像停下來|就會被別人超過",
    ("!【休息】也是進度", 2.4),
    "因為走得遠的人|都知道什麼時候|該【停一下】",
]
TL, SUBS = text_cards(CARDS)       # start= first card's time (default: after the title card), cps= reading speed
o = TL.o
C = [o(t) for _, t, _ in SUBS]     # output second each card appears: start scenes on these

# ---- 2. scenes: fn(c, t, lt, dur). A new picture every 1-2 cards; the picture carries the card's idea. ----
TITLE_PHOTO = None                  # layout.title_bg "photo": a Pexels / Unsplash file in ./assets (ignored with "paper")
def sc_title(c, t, lt, dur):
    title_card(c, t, lt, ["你是不是也覺得", "【休息】很有罪惡感？"], "停一下也沒關係", photo=TITLE_PHOTO)

def sc_guilt(c, t, lt, dur):
    paper_bg(c, t); deco(c, t)
    with Xf(c, 540, 820, eback(prog(lt, 0, 0.45), 1.8)): props.warn_light(c, on=0.5 + 0.5 * math.sin(t * 6))

def sc_rest(c, t, lt, dur):
    paper_bg(c, t, PEACH); deco(c, t, 0.7)
    with Xf(c, 540, 840, eback(prog(lt, 0, 0.45), 1.8)): props.hammock(c, t)

def sc_end(c, t, lt, dur):
    end_card(c, t, lt)

SCENES = ([("title", 0.0, sc_title)] if LAYOUT["title_card"] else []) + [
    ("guilt", C[0] - 0.2, sc_guilt),
    ("rest", C[2] - 0.2, sc_rest),
] + ([("end", TL.END_START, sc_end)] if LAYOUT["end_card"] else [])
SCENES[0] = (SCENES[0][0], 0.0, SCENES[0][2])     # the first scene always starts at 0
# ---- 3. transitions into each scene: circle / slide / zoom / fade / push / cut ----
TRANS = {"guilt": "circle", "rest": "push", "end": "circle"}

R = Reel(HERE, os.path.abspath(OUT), TL, SUBS, SCENES, TRANS)

if __name__ == "__main__":
    R.cli()
