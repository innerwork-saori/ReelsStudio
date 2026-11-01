"""Render a one-page preview of the current brand (brand.json): palette swatches, title card, a subtitle scene
with props, the second-speaker chip, a stock-photo scene (a painted stand-in, nothing downloaded), and the end card — so the user can approve the look before any clip is made.
Follows brand.json layout: no top label / no end card (a punch-card scene instead) when those are switched off.
With the "free" style the tiles show the built-in fallback look; the editor designs each clip itself.

usage: python brand_preview.py [out.png]        default: <brand dir>/brand_preview.png
Uses the brand in REELS_BRAND if set, else <toolkit>/my-brand/.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reels_lib import *            # noqa: F401,F403
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
MID = (ILLU_TOP + ILLU_BOTTOM) // 2 if LAYOUT["subtitle_pos"] == "low" else 620   # centre of the picture area


def frame(fn):
    surf = skia.Surface(W, H)
    with surf as c:
        c.clear(hx(BG)); fn(c)
    return Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGB")


# sample content: EP81 濬浩's planet metaphor (陸地 → 海洋 → 火箭); the globe and rocket come from that clip
LANDS = [(-25, 18, 30), (20, -12, 28), (0, 48, 20), (-50, -28, 20), (45, 30, 18), (-8, -45, 18), (62, -30, 13)]


def circle(r, x=0, y=0):
    p = skia.Path(); p.addCircle(x, y, r); return p


def globe(c, r, rot=20, t=1.0):
    """a planet with land and sea, waves drifting on the sea"""
    c.drawCircle(0, 0, r, P(SKY))
    c.save(); c.clipPath(circle(r), skia.ClipOp.kIntersect, True)
    for i in range(7):
        y = -r * 0.75 + i * r * 0.25; x = ((i * 137 + t * 40) % (r * 1.6)) - r * 0.8
        p = skia.Path(); p.moveTo(x - 40, y); p.quadTo(x - 20, y - 14, x, y); p.quadTo(x + 20, y + 14, x + 40, y)
        c.drawPath(p, P(WHITE, 0.75, stroke=max(3, r * 0.018), raw=True))
    land = None
    for lon, lat, size in LANDS:
        for dl, db, sc in ((0, 0, 1.0), (size * 0.55, size * 0.25, 0.7), (-size * 0.45, -size * 0.3, 0.65)):
            L = math.radians(lon + dl + rot); la = math.radians(lat + db)
            if math.cos(la) * math.cos(L) < 0.02: continue
            rr = r * math.radians(size) * sc; rx = rr * max(0.18, math.cos(L)); ry = rr * max(0.35, math.cos(la))
            q = skia.Path(); q.addOval(skia.Rect.MakeXYWH(r * math.cos(la) * math.sin(L) - rx, -r * math.sin(la) - ry, 2 * rx, 2 * ry))
            land = q if land is None else skia.Op(land, q, skia.PathOp.kUnion_PathOp)
    if land is not None: c.drawPath(land, P(SAGE)); c.drawPath(land, P(INK, 0.55, stroke=max(3, r * 0.012)))
    c.drawPath(skia.Op(circle(r), circle(r * 1.04, -r * 0.2, -r * 0.24), skia.PathOp.kDifference_PathOp), P(INK, 0.13))
    c.restore()
    arc = skia.Path(); arc.addArc(skia.Rect.MakeXYWH(-r * 0.74, -r * 0.74, r * 1.48, r * 1.48), 200, 48)
    c.drawPath(arc, P(WHITE, 0.75, stroke=max(4, r * 0.07), raw=True)); c.drawCircle(0, 0, r, P(INK, stroke=6))


def rocket(c, t=1.0):
    """a little rocket mid-launch"""
    for col, sc in ((RED, 1.0), (ACC, 0.76), (SUN, 0.5)):
        h = 240 * sc * (1 + 0.14 * math.sin(t * 31 + sc * 5)); w = 58 * sc
        p = skia.Path(); p.moveTo(-w, 178); p.cubicTo(-w, 178 + h * 0.4, -w * 0.3, 178 + h * 0.7, 0, 178 + h)
        p.cubicTo(w * 0.3, 178 + h * 0.7, w, 178 + h * 0.4, w, 178); p.close(); c.drawPath(p, P(col))
    for s in (-1, 1):
        p = skia.Path(); p.moveTo(s * 66, 30); p.lineTo(s * 140, 120); p.lineTo(s * 140, 180); p.lineTo(s * 66, 140); p.close()
        c.drawPath(p, P(RED)); c.drawPath(p, P(INK, stroke=6))
    body = skia.Path(); body.moveTo(-70, 150); body.lineTo(-70, -40); body.cubicTo(-70, -130, -35, -190, 0, -230)
    body.cubicTo(35, -190, 70, -130, 70, -40); body.lineTo(70, 150); body.close()
    cap = skia.Path(); cap.addRect(skia.Rect.MakeXYWH(-100, -260, 200, 160))
    rrect(c, -48, 146, 96, 36, 10, P(STEEL)); rrect(c, -48, 146, 96, 36, 10, P(INK, stroke=5))
    hull = skia.Op(body, cap, skia.PathOp.kDifference_PathOp); nose = skia.Op(body, cap, skia.PathOp.kIntersect_PathOp)
    c.drawPath(hull, P(WHITE)); c.drawPath(hull, P(INK, stroke=6)); c.drawLine(-70, 80, 70, 80, P(INK, 0.35, stroke=4))
    c.drawPath(nose, P(ACC)); c.drawPath(nose, P(INK, stroke=6))
    c.drawCircle(0, -20, 36, P(SKY)); c.drawCircle(0, -20, 36, P(INK, stroke=6)); c.drawCircle(-10, -30, 9, P(WHITE, 0.85))


def title(c):
    title_card(c, 2.0, 2.0, ["你發現過", "自己星球上的", "【海洋】嗎？"], "先向內探索", photo=stock_photo_file())


def scene(c):
    paper_bg(c, 1.0); deco(c, 1.0)
    with Xf(c, 540, MID + 20, 1): globe(c, 300, rot=85)          # turned so the sea shows
    with Xf(c, 820, MID - 330, 1, -8): stamp(c, "海洋！", ACC, 80)
    tag(c, 1.0)
    draw_subtitle(c, 2.0, "我的星球上面|還有【海洋】", 0.0, "r")


def speaker(c):
    paper_bg(c, 1.5, SKY); deco(c, 1.5, 0.7)
    with Xf(c, 540, MID - 40, 1.05, 12): rocket(c, 1.5)
    tag(c, 1.5)
    draw_subtitle(c, 2.0, "我開始可以|【向外探索】", 0.0, "h")


def stock_photo():
    """a made-up "stock photo" (dusk over the sea, painted here — nothing is downloaded) so the sheet can show how
    the top label and subtitles sit on real footage from Pexels / Unsplash"""
    w, h = 1080, 1920
    surf = skia.Surface(w, h)
    with surf as c:
        sky = skia.GradientShader.MakeLinear([(0, 0), (0, h * 0.62)], [hx("#2E3B63"), hx("#B9708A"), hx("#F2B27A")], [0, 0.55, 1])
        c.drawRect(skia.Rect.MakeWH(w, h), skia.Paint(Shader=sky))
        c.drawCircle(700, h * 0.47, 300, P("#FFD9A0", 0.5, blur=120)); c.drawCircle(700, h * 0.47, 85, P("#FFE7C2", 0.95, blur=6))
        for y, col, a, bl in ((0.50, "#6B4A6E", 0.9, 10), (0.545, "#4A3654", 0.95, 5)):      # far hills, softly out of focus
            p = skia.Path(); p.moveTo(0, h); p.lineTo(0, h * y)
            for i in range(9): p.quadTo(i * 135 + 67, h * (y - 0.03 * (1 + (i * 37 % 5) / 4)), (i + 1) * 135, h * y)
            p.lineTo(w, h); p.close(); c.drawPath(p, P(col, a, blur=bl))
        sea = skia.GradientShader.MakeLinear([(0, h * 0.6), (0, h)], [hx("#E79C78"), hx("#4B4F74"), hx("#1F2440")], [0, 0.35, 1])
        c.drawRect(skia.Rect.MakeXYWH(0, h * 0.6, w, h * 0.4), skia.Paint(Shader=sea))
        rnd = random.Random(7)
        for _ in range(140):                                  # glitter on the water under the sun
            y = h * 0.6 + rnd.random() ** 1.6 * h * 0.4; spread = 60 + (y - h * 0.6) * 0.9
            x = 700 + rnd.gauss(0, spread * 0.45); ln = 10 + (y - h * 0.6) * 0.08
            c.drawLine(x - ln, y, x + ln, y, P("#FFE2B8", 0.35 + rnd.random() * 0.4, stroke=3 + (y - h * 0.6) * 0.01, blur=1.5))
        for _ in range(9):                                    # bokeh
            c.drawCircle(rnd.uniform(0, w), rnd.uniform(h * 0.62, h), rnd.uniform(30, 80), P("#FFD7A8", rnd.uniform(0.06, 0.14), blur=6))
    a = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
    noise = np.random.default_rng(3).normal(0, 7, a.shape[:2] + (1,))   # film grain, so it reads as a photo
    a[..., :3] = np.clip(a[..., :3] + noise, 0, 255).astype(np.uint8)
    return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType)


def stock_photo_file():
    """the painted photo as a file, for title_card(photo=...) when layout.title_bg is "photo" """
    if LAYOUT["title_bg"] != "photo": return None
    import tempfile
    p = os.path.join(tempfile.gettempdir(), "reels_studio_sample_photo.png")
    stock_photo().save(p, skia.kPNG)
    return p


def stock(c):
    draw_media(c, stock_photo(), k=0.5)
    tag(c, 1.0)
    draw_subtitle(c, 2.0, "原來答案|一直在【我裡面】", 0.0, "r")


def tag(c, t):
    if LAYOUT["top_tag"]: top_tag(c, t, BRAND["tag"] or BRAND["name"])


def end(c):
    if LAYOUT["end_card"]: return end_card(c, 2.5, 2.5)
    paper_bg(c, 2.0, PEACH); deco(c, 2.0, 0.7)              # no end card: the clip ends on its last line
    with Xf(c, 540, MID - 20, 0.8): globe(c, 300, rot=80)
    tag(c, 2.0)
    draw_subtitle(c, 2.0, "!【更遠的地方】", 0.0, "r")


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


def captions(names, width):
    """what each tile is, under the tiles"""
    surf = skia.Surface(width, 44)
    with surf as c:
        c.clear(hx("#FFFFFF"))
        for i, n in enumerate(names): text(c, n, 30 + i * 300 + 150, 32, fit(n, 22, 280), "#6B6461")
    return Image.fromarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).convert("RGB")


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BRAND_DIR, "brand_preview.png")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    shots = [(title, "標題卡（示意照片）" if LAYOUT["title_bg"] == "photo" else "標題卡"), (scene, "字幕＋插圖"), (speaker, "第二位說話者"), (stock, "實拍素材（示意照片）"),
             (end, "結尾卡" if LAYOUT["end_card"] else "最後一句（不用結尾卡）")]
    tiles = [frame(f).resize((300, 533)) for f, _ in shots]
    sw = swatches()
    width = max(sw.width, 30 * 2 + 300 * len(tiles))
    sheet = Image.new("RGB", (width, 533 + 44 + sw.height + 10), "white")
    for i, im in enumerate(tiles): sheet.paste(im, (30 + i * 300, 0))
    sheet.paste(captions([n for _, n in shots], width), (0, 533))
    sheet.paste(sw, ((width - sw.width) // 2, 533 + 44 + 10))
    sheet.save(out)
    print(f"brand: {BRAND['name']} | palette {BRAND['palette']} | font {os.path.basename(FONT_PATH)}")
    print("preview ->", out)
    glyph_warning({ch: [f"「{txt[:20]}」"] for ch, txt in MISSING.items()}, "樣張缺字")


if __name__ == "__main__":
    main()
