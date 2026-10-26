"""Prop library: ready-made objects for illustrated scenes, drawn in the shared style (thick ink outline,
rounded shapes, flat fills). Every prop draws around (0, 0) in local coordinates, so place / scale / rotate it
with Xf, e.g.  with Xf(c, 540, 820, 1.2, -6): mug(c, crack=k, fill=0.6, leak=0, t=t)

No prop draws people, faces or hands (STYLE.md). Animate props through their arguments (k / open_k / fill /
stretch / heat are 0..1 progress values) and make them react to each other, e.g. a weight pressing a box lid.

  weather & time   cloud, lightning, window_cycle, calendar, rainbow, kite, balloon, plane, boat
  feelings         warn_light, gauge*, band (tension), pot (pressure), flame, mug (cracked but refilled),
                   vase (kintsugi healing), knot (tangled), sprout (growth), hammock (rest), pinwheel (breath)
  health & care    hospital_door, monitor, iv_bag, winding_tube, stethoscope, clipboard, capsule, scalpel,
                   pill_bottle, bed, tissue_box, bandaid, mosquito
  home & daily     bowl, cup, slippers, tp_roll, pillow, curtains, tap, wc_door, kettle_pour, beer, magnifier,
                   binoculars, side_mirror (blind spot), box_lid, weight, balance
  work & goals     grad_cap, briefcase, ladder, coins, trophy, badge, check, qmark, book, note, tarot, squiggle
  (* gauge, tape, sticky, stamp, heart, flower, mic, warning_sign, tick, xmark live in reels_lib)
"""
import math, random
import skia
from reels_lib import *            # noqa: F401,F403


def cloud(c, s, col="#B7C0CB"):
    with Xf(c, 0, 0, s):
        for dx, dy, r in ((-110, 10, 80), (-20, -40, 110), (100, 0, 85), (20, 40, 90)): c.drawCircle(dx, dy, r, P(col))
        rrect(c, -190, 20, 380, 90, 45, P(col))

def lightning(c, k):
    p = skia.Path(); p.moveTo(0, 0); p.lineTo(-50, 160); p.lineTo(10, 150); p.lineTo(-40, 330); p.lineTo(80, 120); p.lineTo(20, 130); p.lineTo(60, 0); p.close()
    c.drawPath(p, P(SUN, k)); c.drawPath(p, P(INK, k, stroke=5))

def hospital_door(c, t, glow, label="加護病房"):
    """double ward door with a lit sign above it (glow > 0.5 = sign on)"""
    rrect(c, -330, -420, 660, 860, 20, P("#DDE6EA")); rrect(c, -330, -420, 660, 860, 20, P(INK, stroke=6))
    for x in (-310, 10):
        rrect(c, x, -330, 300, 750, 10, P("#C5D3DA")); rrect(c, x, -330, 300, 750, 10, P(INK, stroke=5))
        rrect(c, x + 70, -240, 160, 200, 12, P("#EAF4F7")); rrect(c, x + 70, -240, 160, 200, 12, P(INK, stroke=4))
    c.drawLine(0, -330, 0, 420, P(INK, stroke=6))
    # sign above the door
    rrect(c, -240, -560, 480, 110, 22, P(RED if glow > 0.5 else "#B5584A"))
    if glow > 0.5: rrect(c, -260, -580, 520, 150, 30, P(RED, 0.35, blur=24))
    rrect(c, -240, -560, 480, 110, 22, P(INK, stroke=6))
    text(c, label, 0, -482, 64, WHITE, bold=2)

def monitor(c, t, k):
    rrect(c, -240, -150, 480, 300, 30, P("#3B4650")); rrect(c, -240, -150, 480, 300, 30, P(INK, stroke=6))
    rrect(c, -210, -120, 420, 240, 16, P("#1E2A30"))
    ecg = skia.Path(); ecg.moveTo(-200, 10)
    for i in range(4):
        x = -200 + i * 105
        ecg.lineTo(x + 40, 10); ecg.lineTo(x + 52, -70); ecg.lineTo(x + 64, 70); ecg.lineTo(x + 76, 10); ecg.lineTo(x + 105, 10)
    c.save(); c.clipPath(rect_path(-210, -120, 420, 240), skia.ClipOp.kIntersect, True)
    phase = (t * 0.8) % 1
    path_part(c, ecg, phase * k, P("#7CF0A8", stroke=7))
    c.restore()
    c.drawCircle(185, -95, 10, P(RED, 0.5 + 0.5 * math.sin(t * 8)))

def iv_bag(c, t):
    c.drawLine(0, -260, 0, 380, P(STEEL, stroke=12)); c.drawLine(-60, -260, 60, -260, P(STEEL, stroke=12))
    rrect(c, -70, -230, 140, 200, 40, P("#EAF4F7", 0.95)); rrect(c, -70, -230, 140, 200, 40, P(INK, stroke=5))
    rrect(c, -60, -140, 120, 100, 30, P(SKY, 0.8))
    c.drawLine(0, -30, 0, 40, P(INK, stroke=5)); rrect(c, -16, 40, 32, 60, 10, P(WHITE)); rrect(c, -16, 40, 32, 60, 10, P(INK, stroke=4))
    ph = (t * 1.6) % 1
    c.drawCircle(0, 55 + ph * 35, 7, P(SKY, 1 - ph))
    tube = skia.Path(); tube.moveTo(0, 100); tube.quadTo(40, 250, 180, 300); c.drawPath(tube, P(INK, 0.5, stroke=4))

def winding_tube(c, t, bleed):
    p = skia.Path(); p.moveTo(-330, -380)
    p.cubicTo(300, -380, 300, -200, 0, -200); p.cubicTo(-330, -200, -330, -20, 0, -20)
    p.cubicTo(330, -20, 330, 160, 0, 160); p.cubicTo(-330, 160, -330, 340, 330, 340)
    c.drawPath(p, P("#F2B8A8", stroke=86)); c.drawPath(p, P(INK, 0.55, stroke=5, dash=[2, 0]))
    c.drawPath(p, P("#F7CFC3", stroke=60))
    m = skia.PathMeasure(p, False); L = m.getLength()
    # flow dots moving through
    for i in range(10):
        pos, _ = m.getPosTan(((t * 0.08 + i / 10) % 1) * L); c.drawCircle(pos.x(), pos.y(), 9, P(WHITE, 0.8))
    if bleed > 0:
        pos, _ = m.getPosTan(L * 0.52)
        for i in range(3):
            ph = (t * 0.9 + i / 3) % 1
            c.drawCircle(pos.x(), pos.y(), 40 + ph * 160 * bleed, P(RED, (1 - ph) * 0.45 * bleed, stroke=10))
        with Xf(c, pos.x(), pos.y(), eback(clamp(bleed), 2)):
            d = skia.Path(); d.moveTo(0, -60); d.cubicTo(45, -10, 45, 40, 0, 45); d.cubicTo(-45, 40, -45, -10, 0, -60); d.close()
            c.drawPath(d, P(RED)); c.drawPath(d, P(INK, stroke=5)); c.drawCircle(-12, 10, 9, P(WHITE, 0.6))

def stethoscope(c, k):
    tube = skia.Path(); tube.moveTo(-150, -260); tube.cubicTo(-200, 40, 150, 40, 120, -260)
    tube.moveTo(-15, 20); tube.cubicTo(-10, 160, 200, 140, 210, 260)
    path_part(c, tube, k, P("#5A6787", stroke=20))
    for x in (-150, 120): c.drawCircle(x, -268, 18 * k, P(INK))
    if k > 0.8:
        c.drawCircle(210, 300, 56, P(STEEL)); c.drawCircle(210, 300, 56, P(INK, stroke=6)); c.drawCircle(210, 300, 30, P(WHITE, 0.7))

def clipboard(c, lines_k):
    rrect(c, -200, -260, 400, 520, 26, P("#C98B55")); rrect(c, -200, -260, 400, 520, 26, P(INK, stroke=6))
    rrect(c, -170, -220, 340, 450, 12, P(WHITE))
    rrect(c, -80, -290, 160, 70, 20, P(STEEL)); rrect(c, -80, -290, 160, 70, 20, P(INK, stroke=5))
    for i in range(6):
        w = 260 * clamp(lines_k * 6 - i)
        if w > 0: c.drawLine(-130, -150 + i * 62, -130 + w, -150 + i * 62, P(GRAY, stroke=12))

def capsule(c, s=1.0, rot=0):
    with Xf(c, 0, 0, s, rot):
        rrect(c, -90, -38, 90, 76, 38, P(ACC)); rrect(c, 0, -38, 90, 76, 38, P(WHITE))
        c.drawRect(skia.Rect.MakeXYWH(-30, -38, 60, 76), P(ACC)); c.drawRect(skia.Rect.MakeXYWH(0, -38, 30, 76), P(WHITE))
        rrect(c, -90, -38, 180, 76, 38, P(INK, stroke=5)); c.drawLine(0, -38, 0, 38, P(INK, stroke=4))
        rrect(c, -70, -24, 50, 14, 7, P(WHITE, 0.5))

def scalpel(c, s=1.0, rot=0):
    with Xf(c, 0, 0, s, rot):
        rrect(c, -150, -18, 170, 36, 12, P(STEEL)); rrect(c, -150, -18, 170, 36, 12, P(INK, stroke=5))
        b = skia.Path(); b.moveTo(20, -18); b.lineTo(130, -18); b.quadTo(160, 0, 120, 22); b.lineTo(20, 18); b.close()
        c.drawPath(b, P("#E9EEF2")); c.drawPath(b, P(INK, stroke=5))

def balance(c, tilt, t, left_fn, right_fn, labels=("A", "B")):
    """scale: tilt in degrees (+ = right side down); left_fn / right_fn draw what sits in each pan"""
    a = math.radians(tilt)
    c.drawLine(0, -180, 0, 330, P("#A86F45", stroke=22)); rrect(c, -140, 320, 280, 40, 16, P("#A86F45")); rrect(c, -140, 320, 280, 40, 16, P(INK, stroke=5))
    lx, ly = -330 * math.cos(a), -180 - 330 * math.sin(a)
    rx, ry = 330 * math.cos(a), -180 + 330 * math.sin(a)
    c.drawLine(lx, ly, rx, ry, P(INK, stroke=14)); c.drawCircle(0, -180, 22, P(SUN)); c.drawCircle(0, -180, 22, P(INK, stroke=5))
    for (x, y, fn, lab) in ((lx, ly, left_fn, labels[0]), (rx, ry, right_fn, labels[1])):
        c.drawLine(x, y, x - 100, y + 160, P(INK, 0.7, stroke=4)); c.drawLine(x, y, x + 100, y + 160, P(INK, 0.7, stroke=4))
        pan = skia.Path(); pan.addArc(skia.Rect.MakeXYWH(x - 130, y + 100, 260, 120), 0, 180); pan.close()
        c.drawPath(pan, P(SUN)); c.drawPath(pan, P(INK, stroke=5))
        with Xf(c, x, y + 120): fn(c)
        text(c, lab, x, y + 300, 54, INK, bold=1.5)

def knot(c, t, k):
    random.seed(4)
    for j, col in enumerate((ROSE, "#E7A792", PEACH)):
        p = skia.Path(); x, y = -380, -200 + j * 140; p.moveTo(x, y)
        for i in range(14):
            nx = random.uniform(-320, 320); ny = random.uniform(-380, 380)
            p.quadTo((x + nx) / 2 + random.uniform(-200, 200), (y + ny) / 2 + random.uniform(-200, 200), nx, ny); x, y = nx, ny
        p.lineTo(400, 200 - j * 140)
        path_part(c, p, k, P(col, stroke=28)); path_part(c, p, k, P(INK, 0.5, stroke=3))
    # glue blobs where the threads stick
    for i in range(6):
        kk = eback(prog(k, 0.5 + i * 0.07, 0.2), 2)
        if kk > 0:
            random.seed(20 + i); x, y = random.uniform(-260, 260), random.uniform(-300, 300)
            c.drawCircle(x, y, 34 * kk, P("#F3E3A2", 0.9)); c.drawCircle(x, y, 34 * kk, P(INK, 0.6, stroke=4))

def pill_bottle(c, open_k, label="用藥"):
    rrect(c, -150, -170, 300, 360, 40, P("#F3A65A", 0.92)); rrect(c, -150, -170, 300, 360, 40, P(INK, stroke=6))
    rrect(c, -120, -60, 240, 150, 16, P(WHITE)); rrect(c, -120, -60, 240, 150, 16, P(INK, stroke=4))
    text(c, label, 0, 40, 72, ACC, bold=2)
    with Xf(c, -70 * open_k, -200 - 130 * open_k, 1, -22 * open_k):
        rrect(c, -170, -60, 340, 70, 20, P(WHITE)); rrect(c, -170, -60, 340, 70, 20, P(INK, stroke=6))
        for x in range(-140, 160, 40): c.drawLine(x, -50, x, 0, P(INK, 0.35, stroke=4))

def vase(c, t, heal):
    p = skia.Path(); p.moveTo(-70, -300); p.lineTo(70, -300); p.quadTo(60, -220, 130, -120)
    p.cubicTo(250, 40, 200, 260, 90, 300); p.lineTo(-90, 300); p.cubicTo(-200, 260, -250, 40, -130, -120); p.quadTo(-60, -220, -70, -300); p.close()
    c.drawPath(p, P("#9FC3D4")); c.drawPath(p, P(INK, stroke=7))
    for i in range(3): c.drawLine(-150 + i * 10, -40 + i * 90, 150 - i * 10, -40 + i * 90, P(WHITE, 0.35, stroke=10))
    cracks = [[(-60, -300), (-20, -180), (-80, -60), (-20, 60), (-90, 180), (-40, 300)],
              [(-20, 60), (80, 110), (120, 220)], [(-80, -60), (-170, 0)]]
    for i, cr in enumerate(cracks):
        q = skia.Path(); q.moveTo(*cr[0])
        for pt in cr[1:]: q.lineTo(*pt)
        c.drawPath(q, P(INK, stroke=6))
        path_part(c, q, clamp(heal * 1.3 - i * 0.15), P("#E9B53D", stroke=14))     # kintsugi gold seams
    if heal > 0.3:
        for i in range(6):
            a = t * 1.5 + i; star4(c, 160 * math.cos(a), -40 + 260 * math.sin(a * 0.7), 18 * heal, SUN)

def calendar(c, t, pages, days_txt):
    rrect(c, -260, -280, 520, 560, 34, P(WHITE)); rrect(c, -260, -280, 520, 560, 34, P(INK, stroke=6))
    rrect(c, -260, -280, 520, 140, 34, P(STEEL)); c.drawRect(skia.Rect.MakeXYWH(-260, -180, 520, 40), P(STEEL))
    for x in (-150, 150): rrect(c, x - 14, -320, 28, 90, 14, P(INK))
    text(c, days_txt, 0, 120, 210, INK, bold=4)
    flip = pages % 1
    if flip > 0.02:
        with Xf(c, 0, -140):
            c.scale(1, max(0.02, 1 - flip))
            rrect(c, -258, 0, 516, 418, 20, P("#F4F1EE")); rrect(c, -258, 0, 516, 418, 20, P(INK, 0.5, stroke=4))

def bowl(c, gray=False):
    col = "#C9C0B8" if gray else ACC
    p = skia.Path(); p.moveTo(-130, -10); p.lineTo(130, -10); p.quadTo(120, 110, 0, 115); p.quadTo(-120, 110, -130, -10); p.close()
    if not gray:
        for dx in (-50, 0, 50): c.drawCircle(dx, -20, 40, P(WHITE))
    c.drawPath(p, P(col)); c.drawPath(p, P(INK, stroke=6)); rrect(c, -40, 110, 80, 20, 8, P(INK))
    c.drawLine(40, -120, 110, 0, P("#A86F45", stroke=8)); c.drawLine(70, -130, 125, -5, P("#A86F45", stroke=8))

def cup(c, fill=0.0, gray=False):
    g = skia.Path(); g.moveTo(-80, -130); g.lineTo(80, -130); g.lineTo(62, 130); g.lineTo(-62, 130); g.close()
    c.drawPath(g, P("#EAF4F7", 0.8))
    if fill > 0:
        c.save(); c.clipPath(g, skia.ClipOp.kIntersect, True)
        c.drawRect(skia.Rect.MakeXYWH(-90, lerp(130, -100, fill), 180, 300), P("#BFE0EC" if gray else SKY)); c.restore()
    c.drawPath(g, P(INK, stroke=6)); c.drawLine(-50, -90, -40, 90, P(WHITE, 0.8, stroke=8))

def slippers(c, gray=False):
    col = "#C9C0B8" if gray else ROSE
    for dx, r in ((-75, -6), (75, 6)):
        with Xf(c, dx, 0, 1, r):
            c.drawOval(skia.Rect.MakeXYWH(-50, -110, 100, 220), P(col)); c.drawOval(skia.Rect.MakeXYWH(-50, -110, 100, 220), P(INK, stroke=5))
            p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(-56, -100, 112, 100), 180, 180); c.drawPath(p, P(WHITE if not gray else "#E4DDD7", stroke=26))

def tp_roll(c, unroll=0.0, gray=False):
    col = "#E4DDD7" if gray else WHITE
    if unroll > 0:
        rrect(c, -10, 40, 120, 260 * unroll, 6, P(col)); rrect(c, -10, 40, 120, 260 * unroll, 6, P(INK, stroke=4))
        for i in range(int(4 * unroll)): c.drawLine(0, 100 + i * 60, 100, 100 + i * 60, P(INK, 0.3, stroke=3, dash=[8, 6]))
    rrect(c, -110, -120, 220, 240, 30, P(col)); rrect(c, -110, -120, 220, 240, 30, P(INK, stroke=6))
    c.drawOval(skia.Rect.MakeXYWH(-110, -150, 220, 70), P(col)); c.drawOval(skia.Rect.MakeXYWH(-110, -150, 220, 70), P(INK, stroke=6))
    c.drawOval(skia.Rect.MakeXYWH(-36, -128, 72, 26), P("#C9A27A"))

def pillow(c, gray=False):
    col = "#C9C0B8" if gray else LILAC
    p = skia.Path(); p.moveTo(-150, -80); p.quadTo(0, -110, 150, -80); p.quadTo(180, 0, 150, 80); p.quadTo(0, 110, -150, 80); p.quadTo(-180, 0, -150, -80); p.close()
    c.drawPath(p, P(col)); c.drawPath(p, P(INK, stroke=6))
    m = skia.Path(); m.addCircle(70, -20, 34); cut = skia.Path(); cut.addCircle(88, -34, 30)
    mm = skia.Op(m, cut, skia.PathOp.kDifference_PathOp); c.drawPath(mm, P(SUN if not gray else "#E4DDD7"))

def bed(c, t):
    rrect(c, -360, -40, 720, 160, 24, P("#DDE6EA")); rrect(c, -360, -40, 720, 160, 24, P(INK, stroke=6))
    rrect(c, -400, -220, 50, 420, 16, P(STEEL)); rrect(c, 350, -120, 50, 320, 16, P(STEEL))
    rrect(c, -340, -110, 200, 80, 30, P(WHITE)); rrect(c, -340, -110, 200, 80, 30, P(INK, stroke=5))
    b = skia.Path(); b.moveTo(-150, -70); b.quadTo(100, -110 + 6 * math.sin(t * 1.2), 360, -60); b.lineTo(360, 30); b.lineTo(-150, 30); b.close()
    c.drawPath(b, P(MINT)); c.drawPath(b, P(INK, stroke=5))
    for x in (-320, 320): c.drawCircle(x, 150, 26, P(INK))

def window_cycle(c, ph):
    """window whose sky cycles day -> night repeatedly (time passing)"""
    rrect(c, -170, -200, 340, 400, 20, P(INK))
    sky = lin(0, -190, 0, 190, ["#2F3350", "#4C4A73"]) if math.sin(ph * 2 * math.pi) < 0 else lin(0, -190, 0, 190, ["#BFE0EC", "#FFF1DE"])
    c.save(); c.clipPath(rect_path(-150, -180, 300, 360), skia.ClipOp.kIntersect, True)
    c.drawPaint(P(WHITE, shader=sky))
    a = ph * 2 * math.pi
    x, y = 200 * math.cos(a + math.pi), 160 - 260 * abs(math.sin(a))
    if math.sin(a) >= 0: c.drawCircle(x, y, 44, P(SUN))
    else: c.drawCircle(x, y, 38, P("#FFF1C9"))
    c.restore()
    c.drawLine(0, -180, 0, 180, P(INK, stroke=10)); c.drawLine(-150, 0, 150, 0, P(INK, stroke=10))

def curtains(c, open_k):
    """full-screen curtains in canvas coordinates (draw without Xf); open_k 0 closed -> 1 open"""
    for s in (-1, 1):
        w = lerp(560, 120, open_k)
        with Xf(c, 540 + s * (540 - w / 2), H / 2):
            rrect(c, -w / 2, -H / 2, w, H, 0, P(ROSE))
            for i in range(1, 5): c.drawLine(-w / 2 + i * w / 5, -H / 2, -w / 2 + i * w / 5, H / 2, P("#D47468", stroke=8))

def sprout(c, t, k):
    # soil + stem growing into a flower, leaves shaped like hearts
    c.drawOval(skia.Rect.MakeXYWH(-260, 230, 520, 120), P("#B98463")); c.drawOval(skia.Rect.MakeXYWH(-260, 230, 520, 120), P(INK, stroke=6))
    stem = skia.Path(); stem.moveTo(0, 280); stem.cubicTo(-40, 120, 50, -20, 0, -200)
    path_part(c, stem, clamp(k * 1.4), P("#6FA77A", stroke=18))
    for i, (y, s) in enumerate(((150, -1), (40, 1))):
        kk = eback(prog(k, 0.25 + i * 0.15, 0.3), 2)
        if kk > 0:
            with Xf(c, s * 10, y, kk, s * 50 - 180): heart(c, 60, SAGE)
    kf = eback(prog(k, 0.6, 0.35), 2)
    if kf > 0:
        with Xf(c, 0, -210, kf * 1.6): flower(c, ACC, t)

def tap(c, t, flow):
    rrect(c, -40, -200, 260, 70, 30, P(STEEL)); rrect(c, -40, -200, 260, 70, 30, P(INK, stroke=6))
    rrect(c, -60, -170, 80, 80, 20, P(STEEL)); rrect(c, -60, -170, 80, 80, 20, P(INK, stroke=6))
    rrect(c, 60, -250, 100, 50, 18, P(ACC)); rrect(c, 60, -250, 100, 50, 18, P(INK, stroke=5))
    if flow > 0:
        rrect(c, -36, -90, 32, 200, 16, P(SKY, 0.9 * flow))
        for i in range(3):
            ph = (t * 3 + i / 3) % 1; c.drawCircle(-20 + 14 * math.sin(i * 3), -80 + ph * 200, 8, P(WHITE, 0.8 * (1 - ph)))

def wc_door(c, open_k):
    rrect(c, -230, -380, 460, 760, 18, P("#C98B55")); rrect(c, -230, -380, 460, 760, 18, P(INK, stroke=6))
    with Xf(c, -200, 0):
        c.scale(max(0.15, 1 - 0.75 * open_k), 1)
        rrect(c, 0, -350, 400, 700, 12, P("#E7B98A")); rrect(c, 0, -350, 400, 700, 12, P(INK, stroke=5))
        rrect(c, 120, -260, 160, 90, 20, P(WHITE)); rrect(c, 120, -260, 160, 90, 20, P(INK, stroke=4))
        text(c, "WC", 200, -198, 60, INK, bold=2)
        c.drawCircle(340, 20, 16, P(SUN))

def warn_light(c, on=1.0, r=70):
    """Dashboard-style warning lamp: round lens with an ! inside."""
    c.drawCircle(0, 0, r + 26, P(INK)); c.drawCircle(0, 0, r + 14, P("#5A4744"))
    c.drawCircle(0, 0, r, P(lerp_col(on)))
    if on > 0.3: c.drawCircle(0, 0, r + 60, P(ACC, 0.35 * on, blur=30))
    text(c, "!", 0, r * 0.45, r * 1.4, WHITE if on > 0.3 else "#9C8F88", bold=4)

def lerp_col(on): return SUN if on > 0.6 else ("#F2A65A" if on > 0.3 else "#7A6A66")

def magnifier(c):
    c.drawLine(70, 70, 150, 150, P("#A86F45", stroke=30))
    c.drawCircle(0, 0, 95, P(WHITE, 0.35)); c.drawCircle(0, 0, 95, P(INK, stroke=16))
    p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(-65, -65, 130, 130), 200, 60); c.drawPath(p, P(WHITE, 0.9, stroke=10))

def tissue_box(c):
    rrect(c, -120, -40, 240, 130, 18, P(SKY)); rrect(c, -120, -40, 240, 130, 18, P(INK, stroke=5))
    rrect(c, -60, -40, 120, 26, 13, P("#7FB5C6"))
    t = skia.Path(); t.moveTo(-40, -36); t.quadTo(-50, -120, 10, -150); t.quadTo(20, -90, 50, -36); t.close()
    c.drawPath(t, P(WHITE)); c.drawPath(t, P(INK, stroke=5))
    for x in (-80, 0, 80): star4(c, x, 30, 14, WHITE, 0.8)

def bandaid(c):
    with Xf(c, 0, 0, 1, -25):
        rrect(c, -130, -40, 260, 80, 40, P("#F2C38F")); rrect(c, -130, -40, 260, 80, 40, P(INK, stroke=5))
        rrect(c, -45, -32, 90, 64, 12, P("#E7A86E"))
        for dx in (-20, 0, 20):
            for dy in (-12, 12): c.drawCircle(dx, dy, 4, P("#C98B55"))

def mosquito(c, t):
    flap = math.sin(t * 60) * 0.5 + 0.5
    for s in (-1, 1):
        with Xf(c, 0, -10, 1, s * (25 + 25 * flap)):
            c.drawOval(skia.Rect.MakeXYWH(-14, -70, 28, 64), P(WHITE, 0.75)); c.drawOval(skia.Rect.MakeXYWH(-14, -70, 28, 64), P(INK, 0.6, stroke=3))
    c.drawOval(skia.Rect.MakeXYWH(-40, -12, 80, 26), P("#6B5650"))
    c.drawCircle(-48, 0, 14, P("#6B5650")); c.drawLine(-60, 4, -95, 22, P(INK, stroke=4))
    for i in range(3):
        c.drawLine(-15 + i * 18, 10, -25 + i * 18, 45, P(INK, stroke=3))
        c.drawLine(-15 + i * 18, 10, -5 + i * 18, 45, P(INK, stroke=3))

def flame(c, s, t, seed):
    k = 1 + 0.15 * math.sin(t * 12 + seed)
    with Xf(c, 0, 0, s):
        for col, sc in ((ACC, 1.0), (SUN, 0.6)):
            p = skia.Path(); h = 110 * k * sc; w = 50 * sc
            p.moveTo(0, 0); p.cubicTo(-w, -h * 0.3, -w * 0.4, -h * 0.7, 0, -h); p.cubicTo(w * 0.4, -h * 0.7, w, -h * 0.3, 0, 0)
            c.drawPath(p, P(col))

def pinwheel(c, ang):
    c.drawLine(0, 0, 0, 380, P("#A86F45", stroke=16))
    with Xf(c, 0, 0, 1, ang):
        for i, col in enumerate((ACC, SUN, SAGE, SKY)):
            with Xf(c, 0, 0, 1, i * 90):
                p = skia.Path(); p.moveTo(0, 0); p.lineTo(0, -160); p.quadTo(110, -120, 120, 0); p.close()
                c.drawPath(p, P(col)); c.drawPath(p, P(INK, stroke=5))
    c.drawCircle(0, 0, 18, P(INK))

def box_lid(c, w, h, lid_y, shake, t):
    dx = shake * math.sin(t * 50)
    with Xf(c, dx, 0):
        rrect(c, -w / 2, -h, w, h, 18, P("#C98B55")); rrect(c, -w / 2, -h, w, h, 18, P(INK, stroke=6))
        c.drawRect(skia.Rect.MakeXYWH(-w / 2, -h * 0.55, w, 22), P("#B07440"))
        with Xf(c, 0, -h - lid_y, 1, shake * 4 * math.sin(t * 37)):
            rrect(c, -w / 2 - 20, -36, w + 40, 44, 14, P("#D9A06A")); rrect(c, -w / 2 - 20, -36, w + 40, 44, 14, P(INK, stroke=6))

def weight(c, lab):
    p = skia.Path(); p.moveTo(-120, 70); p.lineTo(120, 70); p.lineTo(90, -60); p.lineTo(-90, -60); p.close()
    c.drawPath(p, P("#6E6A78")); c.drawPath(p, P(INK, stroke=6))
    c.drawCircle(0, -80, 34, P(INK, stroke=14))
    text(c, lab, 0, 30, 64, WHITE, bold=2)

def mug(c, crack, fill, leak, t):
    # handle
    c.drawCircle(150, 10, 70, P(WHITE, stroke=30)); c.drawCircle(150, 10, 70, P(INK, stroke=5))
    body = skia.Path(); body.moveTo(-140, -150); body.lineTo(140, -150); body.lineTo(120, 150); body.quadTo(0, 175, -120, 150); body.close()
    c.drawPath(body, P(WHITE))
    if fill > 0:
        c.save(); c.clipPath(body, skia.ClipOp.kIntersect, True)
        top = lerp(160, -120, fill)
        wv = skia.Path(); wv.moveTo(-160, top)
        for x in range(-160, 170, 20): wv.lineTo(x, top + 6 * math.sin(x / 25 + t * 6))
        wv.lineTo(170, 200); wv.lineTo(-160, 200); wv.close(); c.drawPath(wv, P("#8A5A3C"))
        c.restore()
    c.drawPath(body, P(INK, stroke=6))
    rrect(c, -150, -170, 300, 30, 15, P(WHITE)); rrect(c, -150, -170, 300, 30, 15, P(INK, stroke=6))
    cr = skia.Path(); cr.moveTo(-40, -150); cr.lineTo(-10, -90); cr.lineTo(-45, -40); cr.lineTo(0, 20); cr.lineTo(-30, 80); cr.lineTo(10, 150)
    path_part(c, cr, crack, P(INK, stroke=6))
    if leak > 0:
        for i in range(3):
            ph = (t * 1.2 + i / 3) % 1
            c.drawCircle(-20 + 10 * i, 160 + ph * 220, 13 * (1 - ph * 0.4), P("#8A5A3C", leak * (1 - ph)))
        c.drawOval(skia.Rect.MakeXYWH(-120, 360, 200 * leak, 34), P("#8A5A3C", 0.55))

def kettle_pour(c, k, t):
    with Xf(c, 0, 0, 1, -38 * k):
        body = skia.Path(); body.addOval(skia.Rect.MakeXYWH(-120, -90, 240, 180)); c.drawPath(body, P(ACC)); c.drawPath(body, P(INK, stroke=6))
        sp = skia.Path(); sp.moveTo(-110, -10); sp.lineTo(-210, -70); sp.lineTo(-200, -90); sp.lineTo(-100, -50); sp.close()
        c.drawPath(sp, P(ACC)); c.drawPath(sp, P(INK, stroke=6))
        p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(-80, -180, 160, 140), 200, 140); c.drawPath(p, P(INK, stroke=14))
        rrect(c, -40, -104, 80, 22, 11, P(INK))

def hammock(c, t):
    for x in (-330, 330):
        c.drawLine(x, -260, x, 260, P("#A86F45", stroke=26))
        blob(c, x, -300, 110, SAGE, 1, t, x)
    sw = 12 * math.sin(t * 1.5)
    net = skia.Path(); net.moveTo(-320, -60); net.quadTo(sw, 160, 320, -60); net.quadTo(sw, 90, -320, -60); net.close()
    c.drawPath(net, P(PEACH)); c.drawPath(net, P(INK, stroke=6))
    for i in range(1, 6):
        x = -320 + i * 107; p = skia.Path(); p.moveTo(x, -60 + 30 * math.sin(i)); p.lineTo(x * 0.8 + sw, 60 + 40 * math.sin(i * 1.3))
        c.drawPath(p, P(INK, 0.35, stroke=4))
    # cobweb in the corner = never used
    with Xf(c, 330, -260):
        for a in range(0, 100, 22):
            r = math.radians(a + 90); c.drawLine(0, 0, 130 * math.cos(r), 130 * math.sin(r), P(INK, 0.4, stroke=3))
        for rr in (40, 80, 120):
            p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(-rr, -rr, 2 * rr, 2 * rr), 90, 90); c.drawPath(p, P(INK, 0.4, stroke=3))

def band(c, stretch, t):
    """rubber band between two pins, more stretch = tighter + vibration + strain lines"""
    hw = lerp(200, 400, stretch)
    vib = stretch * 10 * math.sin(t * 55)
    for x in (-hw, hw):
        c.drawCircle(x, 0, 30, P("#6E6A78")); c.drawCircle(x, 0, 30, P(INK, stroke=5))
    thick = lerp(30, 12, stretch)
    p = skia.Path(); p.moveTo(-hw, -24); p.quadTo(0, -24 + vib + lerp(40, 0, stretch), hw, -24)
    p.moveTo(-hw, 24); p.quadTo(0, 24 - vib - lerp(40, 0, stretch), hw, 24)
    col = SUN if stretch < 0.5 else (ACC if stretch < 0.85 else RED)
    c.drawPath(p, P(col, stroke=thick))
    if stretch > 0.5:
        for s in (-1, 1):
            for i in range(3):
                c.drawLine(s * (hw * 0.3 + i * 50), -80 - i * 10, s * (hw * 0.3 + i * 50 + 20), -120 - i * 10, P(INK, (stretch - 0.5) * 2, stroke=6))

def binoculars(c):
    for x in (-75, 75):
        rrect(c, x - 58, -90, 116, 180, 40, P("#5A6787")); rrect(c, x - 58, -90, 116, 180, 40, P(INK, stroke=6))
        c.drawCircle(x, 90, 62, P(SKY)); c.drawCircle(x, 90, 62, P(INK, stroke=6))
        c.drawCircle(x - 18, 72, 16, P(WHITE, 0.8))
    rrect(c, -30, -50, 60, 70, 12, P(INK))

def beer(c, foam_k):
    rrect(c, -80, -110, 160, 240, 26, P(SUN, 0.92)); rrect(c, -80, -110, 160, 240, 26, P(INK, stroke=6))
    c.drawCircle(105, 0, 50, P(INK, stroke=16))
    for i in range(4): c.drawCircle(-40 + i * 25, 60 - (i % 2) * 50, 8, P(WHITE, 0.7))
    for dx, r in ((-55, 42), (-10, 52), (40, 44)): c.drawCircle(dx, -110, r * foam_k, P(WHITE))
    for dx, r in ((-55, 42), (-10, 52), (40, 44)):
        p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(dx - r * foam_k, -110 - r * foam_k, 2 * r * foam_k, 2 * r * foam_k), 180, 180); c.drawPath(p, P(INK, stroke=5))

def pot(c, heat, t):
    # flames under the pot
    for i, x in enumerate((-110, -40, 30, 100)):
        with Xf(c, x, 210): flame(c, lerp(0.4, 1.1, heat), t, i)
    rrect(c, -200, 150, 400, 40, 14, P("#6E6A78"))
    body = skia.Path(); body.moveTo(-210, -80); body.lineTo(210, -80); body.lineTo(190, 150); body.lineTo(-190, 150); body.close()
    c.drawPath(body, P("#B9C6D6")); c.drawPath(body, P(INK, stroke=6))
    for x in (-250, 250): rrect(c, x - 30, -50, 60, 26, 13, P(INK))
    rrect(c, -230, -110, 460, 40, 20, P("#9FB0C3")); rrect(c, -230, -110, 460, 40, 20, P(INK, stroke=6))
    rrect(c, -30, -150, 60, 44, 14, P(INK))
    # steam
    for i in range(3):
        ph = (t * 0.8 + i / 3) % 1
        s = skia.Path(); x0 = -90 + i * 90; s.moveTo(x0, -170 - ph * 260)
        s.quadTo(x0 + 40, -210 - ph * 260, x0, -250 - ph * 260); s.quadTo(x0 - 40, -290 - ph * 260, x0, -330 - ph * 260)
        c.drawPath(s, P(WHITE, heat * (1 - ph), stroke=14))

def side_mirror(c, t):
    m = skia.Path(); m.addOval(skia.Rect.MakeXYWH(-230, -150, 460, 300))
    c.drawPath(m, P("#5A6787")); c.drawPath(m, P(INK, stroke=8))
    inner = skia.Path(); inner.addOval(skia.Rect.MakeXYWH(-200, -122, 400, 244))
    c.drawPath(inner, P(BG, shader=lin(0, -122, 0, 122, ["#CFE6EE", "#F4EDE4"])))
    c.save(); c.clipPath(inner, skia.ClipOp.kIntersect, True)
    # the blind spot: a fogged-out wedge that hides the red warning light
    c.drawCircle(120, 10, 46, P(RED)); text(c, "!", 120, 30, 60, WHITE, bold=3)
    wedge = skia.Path(); wedge.moveTo(-30, 140); wedge.lineTo(60, -140); wedge.lineTo(260, -140); wedge.lineTo(260, 140); wedge.close()
    c.drawPath(wedge, P("#D8D2CC", 0.94))
    c.restore()
    c.drawPath(inner, P(INK, stroke=5))
    rrect(c, 180, 100, 180, 50, 20, P("#5A6787")); rrect(c, 180, 100, 180, 50, 20, P(INK, stroke=6))

def squiggle(c, x, y, w, color, a, t, sw=7):
    p = skia.Path(); p.moveTo(x, y)
    for i in range(1, 25):
        xx = x + w * i / 24
        p.lineTo(xx, y + 12 * math.sin(i / 24 * 4 * math.pi + t * 3))
    c.drawPath(p, P(color, a, stroke=sw))

def grad_cap(c, gray=False):
    k = (lambda col: "#C9C0B8") if gray else (lambda col: col)
    # diploma
    with Xf(c, 10, 55, 1, -12):
        rrect(c, -95, -22, 190, 44, 22, P(k(WHITE))); rrect(c, -95, -22, 190, 44, 22, P(INK, stroke=5))
        c.drawRect(skia.Rect.MakeXYWH(-14, -22, 28, 44), P(k(ACC)))
    p = skia.Path(); p.moveTo(-60, -20); p.lineTo(60, -20); p.lineTo(52, 20); p.quadTo(0, 34, -52, 20); p.close()
    c.drawPath(p, P(k(INK)))
    d = skia.Path(); d.moveTo(0, -85); d.lineTo(115, -45); d.lineTo(0, -5); d.lineTo(-115, -45); d.close()
    c.drawPath(d, P(k("#4E3B37"))); c.drawPath(d, P(INK, stroke=5))
    c.drawLine(0, -45, 88, -20, P(k(SUN), stroke=7)); c.drawLine(88, -20, 88, 30, P(k(SUN), stroke=7))
    c.drawCircle(88, 36, 12, P(k(SUN))); c.drawCircle(0, -45, 9, P(k(SUN)))

def briefcase(c, gray=False):
    k = (lambda col: "#C9C0B8") if gray else (lambda col: col)
    rrect(c, -45, -95, 90, 50, 20, P(INK, stroke=14))
    rrect(c, -110, -70, 220, 150, 26, P(k("#B8693E")))
    rrect(c, -110, -70, 220, 150, 26, P(INK, stroke=5))
    c.drawRect(skia.Rect.MakeXYWH(-110, -10, 220, 18), P(k("#9A522E")))
    rrect(c, -22, -20, 44, 36, 8, P(k(SUN))); rrect(c, -22, -20, 44, 36, 8, P(INK, stroke=4))

def ladder(c, t=0, gray=False):
    k = (lambda col: "#C9C0B8") if gray else (lambda col: col)
    for x in (-60, 60): c.drawLine(x, 110, x * 0.7, -110, P(k("#C98B55"), stroke=16))
    for i in range(6):
        y = 90 - i * 40; xx = 60 * (1 - (110 - y) / 220 * 0.3)
        c.drawLine(-xx, y, xx, y, P(k("#C98B55"), stroke=12))
    c.drawLine(0, -110, 0, -200, P(INK, stroke=7))
    fl = skia.Path(); w = 8 * math.sin(t * 5)
    fl.moveTo(0, -200); fl.quadTo(40, -205 + w, 75, -190); fl.lineTo(0, -158); fl.close()
    c.drawPath(fl, P(k(ACC)))

def coins(c, gray=False):
    k = (lambda col: "#C9C0B8") if gray else (lambda col: col)
    # money bag
    with Xf(c, -45, -10):
        bag = skia.Path(); bag.moveTo(-30, -70); bag.quadTo(-110, 40, -60, 85); bag.lineTo(60, 85)
        bag.quadTo(110, 40, 30, -70); bag.close()
        c.drawPath(bag, P(k("#E7B98A"))); c.drawPath(bag, P(INK, stroke=5))
        c.drawLine(-34, -68, 34, -68, P(k(ACC), stroke=12))
        e = skia.Path(); e.moveTo(-30, -70); e.lineTo(-45, -100); e.lineTo(0, -85); e.lineTo(45, -100); e.lineTo(30, -70)
        c.drawPath(e, P(k("#E7B98A"))); c.drawPath(e, P(INK, stroke=5))
        text(c, "$", 0, 50, 90, k(ACC), bold=3)
    for i in range(3):
        y = 70 - i * 26
        c.drawOval(skia.Rect.MakeXYWH(40, y - 10, 100, 40), P(k("#D99A1E")))
        c.drawOval(skia.Rect.MakeXYWH(40, y - 20, 100, 40), P(k(SUN)))
        c.drawOval(skia.Rect.MakeXYWH(40, y - 20, 100, 40), P(INK, stroke=4))

def trophy(c, gray=False):
    k = (lambda col: "#C9C0B8") if gray else (lambda col: col)
    c.drawCircle(-70, -60, 32, P(k(SUN), stroke=14)); c.drawCircle(70, -60, 32, P(k(SUN), stroke=14))
    cup = skia.Path(); cup.moveTo(-75, -110); cup.lineTo(75, -110); cup.quadTo(70, 10, 0, 20); cup.quadTo(-70, 10, -75, -110); cup.close()
    c.drawPath(cup, P(k(SUN))); c.drawPath(cup, P(INK, stroke=5))
    c.drawRect(skia.Rect.MakeXYWH(-14, 18, 28, 40), P(k("#D99A1E")))
    rrect(c, -55, 55, 110, 34, 8, P(k("#B8693E"))); rrect(c, -55, 55, 110, 34, 8, P(INK, stroke=5))
    star5(c, 0, -55, 26, WHITE if not gray else "#E4DDD7")

def badge(c, col, r=150, a=1.0):
    c.drawCircle(6, 12, r, P(INK, 0.12 * a, blur=14))
    c.drawCircle(0, 0, r, P(col, a)); c.drawCircle(0, 0, r, P(INK, a * 0.85, stroke=5))

def check(c, x, y, r=34, k=1.0):
    c.drawCircle(x, y, r, P(SAGE)); c.drawCircle(x, y, r, P(INK, stroke=4))
    p = skia.Path(); p.moveTo(x - 15, y + 1); p.lineTo(x - 4, y + 13); p.lineTo(x + 17, y - 12)
    m = skia.PathMeasure(p, False); dst = skia.Path(); m.getSegment(0, m.getLength() * clamp(k), dst, True)
    c.drawPath(dst, P(WHITE, stroke=8))

def qmark(c, x, y, sz, a=1.0, rot=0):
    with Xf(c, x, y, 1, rot, a): text(c, "?", 0, sz * 0.35, sz, ACC, bold=4)

def tarot(c, motif, w=200, h=320, back=False):
    shadow(c, -w / 2, -h / 2, w, h, 22)
    rrect(c, -w / 2, -h / 2, w, h, 22, P("#8E6FB3" if back else WHITE))
    rrect(c, -w / 2, -h / 2, w, h, 22, P(INK, stroke=5))
    rrect(c, -w / 2 + 14, -h / 2 + 14, w - 28, h - 28, 14, P(SUN if not back else "#F3D9A4", stroke=4))
    if back:
        star4(c, 0, 0, 55, "#F3D9A4")
        for dx, dy in ((-50, -100), (50, -100), (-50, 100), (50, 100)): c.drawCircle(dx, dy, 7, P("#F3D9A4"))
        return
    if motif == "sun":
        for i in range(12):
            a = math.radians(i * 30); c.drawLine(28 * math.cos(a), -20 + 28 * math.sin(a), 62 * math.cos(a), -20 + 62 * math.sin(a), P(SUN, stroke=8))
        c.drawCircle(0, -20, 34, P(ACC)); c.drawCircle(0, -20, 34, P(INK, stroke=4))
    elif motif == "moon":
        m = skia.Path(); m.addCircle(0, -20, 50)
        cut = skia.Path(); cut.addCircle(24, -36, 46)
        mm = skia.Op(m, cut, skia.PathOp.kDifference_PathOp)
        c.drawPath(mm, P(SUN)); c.drawPath(mm, P(INK, stroke=4))
        star4(c, 45, 30, 14, LILAC)
    else:
        star5(c, 0, -20, 55, SUN); star4(c, -55, 60, 14, ROSE); star4(c, 55, 50, 10, SAGE)
    c.drawLine(-50, h / 2 - 50, 50, h / 2 - 50, P(INK, 0.5, stroke=5))

def book(c, t, open_k=1.0):
    for side in (-1, 1):
        p = skia.Path(); p.moveTo(0, 20); p.quadTo(side * 90, -10 * open_k - 20, side * 190, 0)
        p.lineTo(side * 190, 120); p.quadTo(side * 90, 100, 0, 130); p.close()
        c.drawPath(p, P(WHITE)); c.drawPath(p, P(INK, stroke=5))
        for i in range(4):
            y = 25 + i * 22; ln = skia.Path(); ln.moveTo(side * 30, y + 12); ln.quadTo(side * 90, y - 4, side * 160, y + 8)
            c.drawPath(ln, P(GRAY, stroke=5))
    c.drawLine(0, 20, 0, 130, P(INK, stroke=5))

def boat(c):
    hull = skia.Path(); hull.moveTo(-110, 0); hull.lineTo(110, 0); hull.lineTo(70, 50); hull.lineTo(-70, 50); hull.close()
    c.drawPath(hull, P(WHITE)); c.drawPath(hull, P(INK, stroke=5))
    sail = skia.Path(); sail.moveTo(-5, -10); sail.lineTo(-5, -150); sail.lineTo(80, -10); sail.close()
    c.drawPath(sail, P(ACC)); c.drawPath(sail, P(INK, stroke=5))
    s2 = skia.Path(); s2.moveTo(-15, -10); s2.lineTo(-15, -110); s2.lineTo(-75, -10); s2.close()
    c.drawPath(s2, P(SUN)); c.drawPath(s2, P(INK, stroke=5))

def balloon(c, col, t, seed):
    sway = 10 * math.sin(t * 2 + seed)
    p = skia.Path(); p.moveTo(0, 60); p.quadTo(sway, 120, -sway, 190); c.drawPath(p, P(INK, stroke=3))
    c.drawOval(skia.Rect.MakeXYWH(-48, -60, 96, 120), P(col)); c.drawOval(skia.Rect.MakeXYWH(-48, -60, 96, 120), P(INK, stroke=4))
    c.drawOval(skia.Rect.MakeXYWH(-28, -42, 18, 32), P(WHITE, 0.6))
    tri = skia.Path(); tri.moveTo(-9, 70); tri.lineTo(9, 70); tri.lineTo(0, 58); tri.close(); c.drawPath(tri, P(col))

def kite(c, t):
    k = skia.Path(); k.moveTo(0, -90); k.lineTo(65, -10); k.lineTo(0, 110); k.lineTo(-65, -10); k.close()
    c.drawPath(k, P(ROSE)); c.drawPath(k, P(INK, stroke=5))
    c.drawLine(0, -90, 0, 110, P(INK, stroke=3)); c.drawLine(-65, -10, 65, -10, P(INK, stroke=3))
    tail = skia.Path(); tail.moveTo(0, 110)
    for i in range(1, 6): tail.lineTo(18 * math.sin(t * 4 + i), 110 + i * 32)
    c.drawPath(tail, P(INK, stroke=3))
    for i in (2, 4): star4(c, 18 * math.sin(t * 4 + i), 110 + i * 32, 12, SUN)

def rainbow(c):
    for i, col in enumerate((ROSE, SUN, SAGE, SKY)):
        r = 130 - i * 24
        p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(-r, -r, 2 * r, 2 * r), 180, 180); c.drawPath(p, P(col, stroke=24))
    for x in (-120, 120):
        for dx, r in ((-28, 26), (0, 34), (28, 26)): c.drawCircle(x + dx, 6, r, P(WHITE))

def plane(c):
    p = skia.Path(); p.moveTo(-90, 0); p.lineTo(100, -50); p.lineTo(-10, 40); p.close()
    c.drawPath(p, P(WHITE)); c.drawPath(p, P(INK, stroke=5))
    q = skia.Path(); q.moveTo(-10, 40); q.lineTo(100, -50); q.lineTo(10, 70); q.close()
    c.drawPath(q, P("#E9E1F7")); c.drawPath(q, P(INK, stroke=5))

def note(c, col):
    c.drawLine(18, 30, 18, -60, P(INK, stroke=7)); c.drawLine(18, -60, 50, -45, P(INK, stroke=7))
    c.drawOval(skia.Rect.MakeXYWH(-14, 14, 36, 28), P(col)); c.drawOval(skia.Rect.MakeXYWH(-14, 14, 36, 28), P(INK, stroke=4))
