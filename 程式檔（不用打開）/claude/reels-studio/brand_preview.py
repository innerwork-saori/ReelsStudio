"""Render a one-page preview of the current brand (brand.json): palette swatches, title card, a subtitle scene
with props, the second-speaker chip, and the end card — so the user can approve the look before any clip is made.
Follows brand.json layout: no top label / no end card (a punch-card scene instead) when those are switched off.
With the "free" style the tiles show the built-in fallback look; the editor designs each clip itself.

usage: python brand_preview.py [out.png]        default: <brand dir>/brand_preview.png
Uses the brand in REELS_BRAND if set, else <toolkit>/my-brand/.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reels_lib import *            # noqa: F401,F403
import props
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MID = (ILLU_TOP + ILLU_BOTTOM) // 2 if LAYOUT["subtitle_pos"] == "low" else 620   # centre of the picture area


def frame(fn):
    surf = skia.Surface(W, H)
    with surf as c:
        c.clear(hx(BG)); fn(c)
    return Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGB")


def title(c):
    title_card(c, 2.0, 2.0, ["你有沒有想過", "「【休息】」也是", "一種能力？"], "真的嗎")


def scene(c):
    paper_bg(c, 1.0); deco(c, 1.0)
    with Xf(c, 540, MID + 20, 1.25): props.mug(c, crack=0.8, fill=0.6, leak=0.4, t=1.0)
    with Xf(c, 830, MID - 320, 1, -8): stamp(c, "撐住", ACC, 80)
    tag(c, 1.0)
    draw_subtitle(c, 2.0, "明明已經【裂開】了|還是每天裝滿", 0.0, "r")


def speaker(c):
    paper_bg(c, 1.5, SKY); deco(c, 1.5, 0.7)
    with Xf(c, 540, MID - 20, 1.3): props.sprout(c, 1.5, 0.9)
    tag(c, 1.5)
    draw_subtitle(c, 2.0, "那你後來|怎麼【轉念】的？", 0.0, "h")


def tag(c, t):
    if LAYOUT["top_tag"]: top_tag(c, t, BRAND["tag"] or BRAND["name"])


def end(c):
    if LAYOUT["end_card"]: return end_card(c, 2.5, 2.5)
    paper_bg(c, 2.0, PEACH); deco(c, 2.0, 0.7)              # no end card: the clip ends on its last line
    with Xf(c, 540, MID - 20, 1.3): props.pillow(c)
    tag(c, 2.0)
    draw_subtitle(c, 2.0, "!【先停一下】", 0.0, "r")


def swatches():
    names = ["bg", "ink", "accent", "highlight", "alert", "ok", "peach", "rose", "sage", "sky", "lilac", "gray"]
    vals = [BG, INK, ACC, SUN, RED, GREEN, PEACH, ROSE, SAGE, SKY, LILAC, GRAY]
    surf = skia.Surface(4 * 300 + 60, 150)
    with surf as c:
        c.clear(hx("#FFFFFF"))
        for i, (n, v) in enumerate(zip(names, vals)):
            x = 30 + i * 100
            rrect(c, x, 20, 80, 80, 16, P(v)); rrect(c, x, 20, 80, 80, 16, P(INK, 0.5, stroke=3))
            text(c, n, x + 40, 128, 20, INK)
    return Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGB")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BRAND_DIR, "brand_preview.png")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tiles = [frame(f).resize((300, 533)) for f in (title, scene, speaker, end)]
    sw = swatches()
    sheet = Image.new("RGB", (sw.width, 533 + sw.height + 20), "white")
    for i, im in enumerate(tiles): sheet.paste(im, (30 + i * 300, 0))
    sheet.paste(sw, (0, 533 + 20))
    sheet.save(out)
    print(f"brand: {BRAND['name']} | palette {BRAND['palette']} | font {os.path.basename(FONT_PATH)}")
    print("preview ->", out)
    glyph_warning({ch: [f"「{txt[:20]}」"] for ch, txt in MISSING.items()}, "樣張缺字")


if __name__ == "__main__":
    main()
