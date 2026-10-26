"""Clip script template (face mode: the speaker filmed themselves) —
copy to <video folder>/_reels_work/clipN/clip.py and fill in the 4 marked blocks.

The picture follows the audio edit automatically: R.face(c, t) shows the source frame for the SOURCE second
being heard, so every cut in KEEPS becomes a jump cut. Mix freely with illustrated / Pexels scenes for the
abstract parts (STYLE.md §10 has the rhythm rules).

  python clip.py audio    -> check every cut prints OK, else move it into a silence from words.py output
  python clip.py sheet    -> READ sheet_*.png: face in frame? not sideways? subtitle not on the mouth?
  python clip.py render   -> final MP4 + verify
"""
import math, os, sys, random
sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "reels-studio"))
from reels_lib import *            # noqa: F401,F403
import props

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.abspath(os.path.join(HERE, "..", "..", "RECORDING.mp4"))   # <- the same file given to words.py
OUT = os.path.join(HERE, "..", "..", "RECORDING_Reels_片段N.mp4")

# ---- 1. edit (source seconds). Jump cuts are visible here, so cut whole sentences / long pauses, not single
#         「嗯」 inside a sentence (a 0.2 s jump in the picture looks like a glitch). ----
TL = Timeline(
    keeps=[(2.10, 9.80), (10.40, 21.30), (22.00, 34.60)],
    seg_t0=0.0,
    end_hold=0.4,
)

# ---- 2. subtitles: same rules as TEMPLATE_clip.py ----
SUBS = [
    ("第一句字幕|【關鍵字】在這裡", 2.15, "r"),
    ("!【金句】", 30.00, "r"),
]

# ---- 3. scenes ----
FOCUS = (0.5, 0.40)     # where the face sits in the source frame (landscape shots get cropped to 9:16 around it)
PUNCH = 1.12            # every other KEEPS range is zoomed in, so jump cuts read as deliberate

def sc_title(c, t, lt, dur):                                  # hook card over the speaker
    title_card(c, t, lt, ["你是不是也", "一直在【等準備好】？"], "別等了", bg=lambda c: R.face(c, t, focus=FOCUS))

def sc_talk(c, t, lt, dur):                                   # plain talking head
    R.face(c, t, focus=FOCUS, punch=PUNCH)

def sc_talk_prop(c, t, lt, dur):                              # talking head + one prop reacting to a word
    R.face(c, t, focus=FOCUS, punch=PUNCH)
    beat = R.L("talk_prop", 14.20)
    if lt > beat:
        with Xf(c, 820, 560, eback(prog(lt, beat, 0.35), 2.2), -6): props.warn_light(c, on=1.0)

def sc_broll(c, t, lt, dur):                                  # abstract idea -> full-bleed illustration, voice continues
    paper_bg(c, t); deco(c, t)
    with Xf(c, 540, 820, 1.3): props.sprout(c, t, prog(lt, 0, dur * 0.8))

def sc_pip(c, t, lt, dur):                                    # illustration with the speaker as a polaroid
    paper_bg(c, t, SKY); deco(c, t, 0.6)
    with Xf(c, 300, 760, 1.1, -5): props.calendar(c, t, prog(lt, 0, dur) * 3, "30")
    R.face(c, t, rect=(560, 520, 420, 560), radius=24, card=True, focus=FOCUS)

def sc_end(c, t, lt, dur):
    end_card(c, t, lt)

SCENES = [
    ("title", 0.0, sc_title),
    ("talk", 3.0, sc_talk),
    ("talk_prop", 9.0, sc_talk_prop),
    ("broll", 16.0, sc_broll),
    ("pip", 20.0, sc_pip),
    ("talk2", 25.0, sc_talk),
    ("end", TL.END_START, sc_end),
]
# ---- 4. transitions: face -> face uses 'cut'; into / out of illustrations rotate circle / slide / zoom ----
TRANS = {"talk": "cut", "talk_prop": "cut", "broll": "circle", "pip": "slide", "talk2": "zoom", "end": "circle"}

R = Reel(HERE, os.path.abspath(OUT), TL, SUBS, SCENES, TRANS, source_video=SRC)   # rotate=90 if the file is tagged wrong

if __name__ == "__main__":
    R.cli()
