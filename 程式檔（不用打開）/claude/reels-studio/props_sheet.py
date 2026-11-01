"""Picture of every prop in props.py, for the panel's 常見問題 (and for a quick look while drawing).

  python props_sheet.py out.png          colours follow REELS_BRAND (the panel passes the current style)
  python props_sheet.py --check          list props that have no Chinese name / sample pose here yet

Categories and order come from the list at the top of props.py, so a new prop shows up on its own once it is
listed there. Give it a Chinese name and a good-looking pose in SAMPLES below; until then it is drawn with
guessed arguments and only its code name.
"""
import inspect, math, os, re, sys
import numpy as np
import skia
import props
from props import *                # noqa: F401,F403

T = 1.2
GROUP_ZH = {"weather & time": "天氣與時間", "feelings": "情緒與狀態", "health & care": "醫療與照護",
            "home & daily": "居家日常", "work & goals": "工作與目標"}

# name: (中文, how to draw it for the picture)
SAMPLES = {
    "cloud": ("雲", lambda c: cloud(c, 1.0)),
    "lightning": ("閃電", lambda c: lightning(c, 1.0)),
    "window_cycle": ("窗外日夜", lambda c: window_cycle(c, 0.3)),
    "calendar": ("日曆", lambda c: calendar(c, T, 1.5, "30")),
    "rainbow": ("彩虹", lambda c: rainbow(c)),
    "kite": ("風箏", lambda c: kite(c, T)),
    "balloon": ("氣球", lambda c: balloon(c, ROSE, T, 1)),
    "plane": ("紙飛機", lambda c: plane(c)),
    "boat": ("紙船", lambda c: boat(c)),
    "warn_light": ("警示燈", lambda c: warn_light(c, 1.0)),
    "band": ("橡皮筋（緊繃）", lambda c: band(c, 0.8, T)),
    "pot": ("鍋子（壓力）", lambda c: pot(c, 0.8, T)),
    "flame": ("火焰", lambda c: flame(c, 1.0, T, 1)),
    "mug": ("裂開的馬克杯", lambda c: mug(c, 1.0, 0.6, 0.5, T)),
    "vase": ("金繼花瓶", lambda c: vase(c, T, 0.8)),
    "knot": ("打結", lambda c: knot(c, T, 0.5)),
    "sprout": ("發芽", lambda c: sprout(c, T, 1.0)),
    "hammock": ("吊床（休息）", lambda c: hammock(c, T)),
    "pinwheel": ("風車（呼吸）", lambda c: pinwheel(c, 20)),
    "hospital_door": ("病房門", lambda c: hospital_door(c, T, 1.0)),
    "monitor": ("心電圖", lambda c: monitor(c, T, 1.0)),
    "iv_bag": ("點滴", lambda c: iv_bag(c, T)),
    "winding_tube": ("管線", lambda c: winding_tube(c, T, 0.6)),
    "stethoscope": ("聽診器", lambda c: stethoscope(c, 1.0)),
    "clipboard": ("病歷板", lambda c: clipboard(c, 1.0)),
    "capsule": ("膠囊", lambda c: capsule(c)),
    "scalpel": ("手術刀", lambda c: scalpel(c)),
    "pill_bottle": ("藥罐", lambda c: pill_bottle(c, 0.6)),
    "bed": ("病床", lambda c: bed(c, T)),
    "tissue_box": ("面紙盒", lambda c: tissue_box(c)),
    "bandaid": ("OK 繃", lambda c: bandaid(c)),
    "mosquito": ("蚊子", lambda c: mosquito(c, T)),
    "bowl": ("碗", lambda c: bowl(c)),
    "cup": ("杯子", lambda c: cup(c, 0.6)),
    "slippers": ("拖鞋", lambda c: slippers(c)),
    "tp_roll": ("衛生紙", lambda c: tp_roll(c, 0.5)),
    "pillow": ("枕頭", lambda c: pillow(c)),
    "curtains": ("窗簾", lambda c: curtains(c, 0.5)),
    "tap": ("水龍頭", lambda c: tap(c, T, 1.0)),
    "wc_door": ("廁所門", lambda c: wc_door(c, 0.4)),
    "kettle_pour": ("倒水壺", lambda c: kettle_pour(c, 0.7, T)),
    "beer": ("啤酒", lambda c: beer(c, 1.0)),
    "magnifier": ("放大鏡", lambda c: magnifier(c)),
    "binoculars": ("望遠鏡", lambda c: binoculars(c)),
    "side_mirror": ("後照鏡（盲點）", lambda c: side_mirror(c, T)),
    "box_lid": ("快爆開的箱子", lambda c: box_lid(c, 360, 260, 30, 0.6, T)),
    "weight": ("秤砣", lambda c: weight(c, "10kg")),
    "balance": ("天秤", lambda c: balance(c, 12, T, lambda c: coins(c), lambda c: heart(c, 60, ROSE), ("錢", "心"))),
    "grad_cap": ("學士帽", lambda c: grad_cap(c)),
    "briefcase": ("公事包", lambda c: briefcase(c)),
    "ladder": ("梯子", lambda c: ladder(c)),
    "coins": ("硬幣", lambda c: coins(c)),
    "trophy": ("獎盃", lambda c: trophy(c)),
    "badge": ("圓形徽章", lambda c: badge(c, SUN)),
    "check": ("打勾", lambda c: check(c, 0, 0, 80)),
    "qmark": ("問號", lambda c: qmark(c, 0, 0, 260)),
    "book": ("書", lambda c: book(c, T)),
    "note": ("音符", lambda c: note(c, ACC)),
    "tarot": ("塔羅牌", lambda c: tarot(c, "sun")),
    "squiggle": ("手繪線", lambda c: squiggle(c, -200, 0, 400, ACC, 1.0, T)),
}

def groups():
    """[(category, [prop names])] from the list in props.py's docstring; props marked * live in reels_lib"""
    out, cur = [], None
    for line in (props.__doc__ or "").splitlines():
        m = re.match(r"\s{2}(\S.*?\S)\s{2,}(\S.*)$", line)
        if m and m.group(1) in GROUP_ZH: cur = (m.group(1), []); out.append(cur); rest = m.group(2)
        elif cur and re.match(r"\s{10,}\S", line): rest = line
        else: cur = None; continue
        cur[1].extend(n.split("(")[0].strip() for n in rest.split(",") if n.strip() and "*" not in n)
    names = [n for n in (x for _, ns in out for x in ns) if n]
    for _, ns in out: ns[:] = [n for n in ns if n and callable(getattr(props, n, None))]
    # drawn in props.py but missing from the docstring list: still show them
    own = [n for n, f in inspect.getmembers(props, inspect.isfunction)
           if f.__module__ == "props" and not n.startswith("_") and n not in names and n != "lerp_col"]
    if own: out.append(("unlisted", own))
    return [(g, ns) for g, ns in out if ns]

def guess(name):
    """draw a prop with no sample yet: fill required arguments by their names"""
    fn = getattr(props, name)
    args = []
    for p in inspect.signature(fn).parameters.values():
        if p.name == "c" or p.default is not inspect.Parameter.empty: continue
        n = p.name
        args.append(T if n == "t" else ACC if n in ("col", "color") else 0 if n in ("x", "y", "seed", "rot")
                    else "A" if n in ("lab", "label", "txt", "motif") else 300 if n in ("w", "h", "sz") else 0.7)
    return lambda c: fn(c, *args)

def render(fn):
    S = 1600
    s = skia.Surface(S, S); c = s.getCanvas(); c.clear(skia.Color4f(0, 0, 0, 0))
    with Xf(c, S / 2, S / 2): fn(c)
    img = s.makeImageSnapshot()
    ys, xs = np.nonzero(img.toarray()[:, :, 3] > 8)
    if len(xs) == 0: return img, (0, 0, 1, 1)
    return img, (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)

def sheet(out):
    gs = groups()
    COLS, CW, CH, PAD, HEAD = 6, 300, 330, 24, 90
    rows = sum(math.ceil(len(ns) / COLS) for _, ns in gs)
    SW, SH = COLS * CW + PAD * 2, 140 + len(gs) * HEAD + rows * CH + PAD
    surf = skia.Surface(SW, SH); c = surf.getCanvas()
    c.drawRect(skia.Rect.MakeWH(SW, SH), P(BG))
    total = sum(len(ns) for _, ns in gs)
    text(c, f"現成道具一覽（{total} 個）", SW / 2, 90, 60, INK, bold=2)
    y = 140
    for g, ns in gs:
        text(c, f"{GROUP_ZH.get(g, '其他')}（{len(ns)}）", PAD + 10, y + 60, 44, ACC, align="l", bold=1.5)
        y += HEAD
        for i, name in enumerate(ns):
            x0, y0 = PAD + i % COLS * CW, y + i // COLS * CH
            rrect(c, x0 + 8, y0 + 8, CW - 16, CH - 16, 22, P(WHITE, 0.75))
            zh, fn = SAMPLES.get(name, (None, None))
            try:
                img, (l, t, r, b) = render(fn or guess(name))
                k = min((CW - 60) / (r - l), (CH - 100) / (b - t), 1.0)
                dw, dh = (r - l) * k, (b - t) * k
                c.drawImageRect(img, skia.Rect(l, t, r, b), skia.Rect.MakeXYWH(x0 + (CW - dw) / 2, y0 + 20 + (CH - 90 - dh) / 2, dw, dh),
                                skia.SamplingOptions(skia.FilterMode.kLinear))
            except Exception as e:
                print(f"props_sheet: {name} could not be drawn: {e}", file=sys.stderr)
            label = f"{zh}　{name}" if zh else name
            text(c, label, x0 + CW / 2, y0 + CH - 30, fit(label, 26, CW - 30), INK, bold=1)
        y += math.ceil(len(ns) / COLS) * CH
    surf.makeImageSnapshot().save(out, skia.kPNG)
    return total

if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        listed = [n for _, ns in groups() for n in ns]
        missing = [n for n in listed if n not in SAMPLES]
        unlisted = [n for g, ns in groups() if g == "unlisted" for n in ns]
        print(f"{len(listed)} props")
        if missing: print("no Chinese name / sample pose in props_sheet.SAMPLES:", ", ".join(missing))
        if unlisted: print("not in the list at the top of props.py:", ", ".join(unlisted))
        sys.exit(1 if missing or unlisted else 0)
    print("ok", sheet(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "props_sheet.png")))
