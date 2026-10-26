"""Reels engine (Reels Studio): Skia drawing -> PyAV H.264/AAC, 1080x1920 @30fps.

A clip script (see TEMPLATE_clip.py) only defines: the edit (KEEPS), subtitles, scene functions and the
scene list, then calls Reel(...).cli().  Everything shared lives here so every Reel looks like one series:
palette, font, decorations, subtitle box, top tag, title card, transitions, end card, audio build, encode.

The channel's look comes from brand.json (see BRAND_DIR below; written by the reels-studio setup interview):
name, palette preset + colour overrides, font, end card. Without a brand.json the defaults below are used.

Two picture modes, freely mixed inside one clip:
  illustrated  scenes drawn with shapes / props.py / Pexels media (audio-only sources)
  face         the speaker's own footage, frame-synced to the audio edit: Reel(..., source_video=...) + R.face()

CLI of a clip script:
  python clip.py audio            build clip_audio.wav from seg.wav + KEEPS (prints dB at every cut)
  python clip.py sheet            preview frame at 70% of every scene -> sheet_*.png contact sheets (read them!)
  python clip.py preview 3.2 7.5  specific seconds -> preview_XX.XX.png
  python clip.py render           full MP4 (+ verify)
"""
import math, os, sys, random, glob, json
import numpy as np, skia, av, soundfile as sf

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- brand (brand.json) ----------------
def _project_brand():
    """channel picked in the Reels Studio panel: "brand" in <material folder>\\_reels_studio.json, looked up from the
    running script's folder (clip.py lives in <material>\\_reels_work\\clipN\\) and the working folder, a few levels up"""
    starts = [os.path.dirname(os.path.abspath(sys.argv[0])) if sys.argv and sys.argv[0] else None, os.getcwd()]
    for d in filter(None, starts):
        for _ in range(4):
            p = os.path.join(d, "_reels_studio.json")
            if os.path.exists(p):
                try: b = json.load(open(p, encoding="utf-8")).get("brand")
                except Exception: b = None
                if b:
                    b = b if os.path.isabs(b) else os.path.join(HERE, b)
                    if os.path.isdir(b): return b
                    print(f"[reels_lib] channel folder {b} (from {p}) not found, using my-brand")
                break
            if os.path.dirname(d) == d: break
            d = os.path.dirname(d)
    return None

BRAND_DIR = os.environ.get("REELS_BRAND") or _project_brand() or os.path.join(HERE, "my-brand")
PALETTES = {   # light backgrounds only: subtitles, ink outlines and decorations assume a pale paper
    "cream": dict(bg="#FFF6EC", ink="#3D2C29", accent="#EF6F3C", highlight="#F7B538", peach="#F9C9B0", rose="#E98A7E",
                  sage="#9CC5A1", sky="#A8D5E2", lilac="#CFC4EC", alert="#E2533B", ok="#7DB88A", gray="#CBC2BA"),
    "mint":  dict(bg="#F3FAF6", ink="#23413A", accent="#2E9E83", highlight="#F6C445", peach="#FBD3B9", rose="#EE8F84",
                  sage="#A6D3B8", sky="#9ED2E6", lilac="#CBC6EE", alert="#E2533B", ok="#5DAE7E", gray="#C3CCC7"),
    "sky":   dict(bg="#F2F7FC", ink="#1F3350", accent="#3A7BD5", highlight="#FFC94A", peach="#F8CDB6", rose="#EF8E9C",
                  sage="#A9CFB0", sky="#A9D3F0", lilac="#C9C3F0", alert="#E2533B", ok="#5DAE7E", gray="#C2CAD4"),
    "blush": dict(bg="#FFF3F3", ink="#4A2C3A", accent="#E2587A", highlight="#F7C04A", peach="#FAC8B4", rose="#F0A0B0",
                  sage="#A8CFA8", sky="#AAD4E4", lilac="#D8C6EE", alert="#D9433B", ok="#6FB28A", gray="#D2C3C8"),
    "mono":  dict(bg="#F7F6F3", ink="#222222", accent="#FF5A36", highlight="#FFD23F", peach="#EDE6DF", rose="#F2B5A7",
                  sage="#C8D5C0", sky="#CFDDE6", lilac="#DAD5EA", alert="#E0412F", ok="#5FA777", gray="#CCCAC5"),
}
BRAND_DEFAULTS = {
    "name": "我的頻道",              # top tag + end card title
    "tag": None,                     # top tag text; None -> name
    "palette": "cream",              # a PALETTES key
    "colors": {},                    # per-role overrides, e.g. {"accent": "#E2587A"}
    "font": "jf-openhuninn-1.1.ttf", # installed font: family name as `fonts.py list` prints it, file name, or path
    "font_weight": 400,              # used with a family name: 400 regular, 500 medium, 700 bold ...
    "speaker_label": "主持人",       # chip on who="h" subtitles
    "end_card": {"icon": "play",     # mic | play | heart | star | logo (the channel folder's logo.png) | none
                 "logo_shape": "original",   # for icon "logo": original | circle | rounded
                 "badge": "",        # short sticker above the name, e.g. 「嗨！」 ('' = none)
                 "cta": "看完整版", "sub": "連結在個人檔案", "guest_prefix": "本集來賓"},
    "style": {},                     # layout look: {"preset": <STYLE_PRESETS key>, <STYLE_OPTIONS key>: <option>, ...}
}

# Layout looks (the panel's 版面風格). A preset fills every element; keys given next to it override that one element.
# No "style" in brand.json = handmade, the original look.
STYLE_OPTIONS = {
    "subtitle":   ["box", "outline", "pill", "dark"],        # white framed box / outlined text, no box / a pill per line / dark box
    "title":      ["note", "bold", "line", "magazine"],      # taped note card / big text, no card / thin-frame card / colour slab
    "background": ["blobs", "plain", "grid", "gradient"],    # hand-drawn blobs + sparkles / flat / notebook grid / soft gradient
    "line":       ["bold", "thin", "soft"],                  # illustration outlines: thick ink / thin ink / thin and faded
    "motion":     ["bouncy", "snappy", "gentle"],            # overshoot of every pop-in + transition length
    "end":        ["classic", "minimal", "card"],            # end card layout
}
STYLE_PRESETS = {
    "handmade": {"subtitle": "box", "title": "note", "background": "blobs", "line": "bold", "motion": "bouncy", "end": "classic"},
    "clean":    {"subtitle": "pill", "title": "line", "background": "plain", "line": "thin", "motion": "snappy", "end": "minimal"},
    "magazine": {"subtitle": "dark", "title": "magazine", "background": "gradient", "line": "thin", "motion": "gentle", "end": "card"},
    "notebook": {"subtitle": "pill", "title": "note", "background": "grid", "line": "soft", "motion": "gentle", "end": "card"},
    "street":   {"subtitle": "outline", "title": "bold", "background": "plain", "line": "bold", "motion": "bouncy", "end": "classic"},
}

def load_brand():
    b = json.loads(json.dumps(BRAND_DEFAULTS))
    p = os.path.join(BRAND_DIR, "brand.json")
    if os.path.exists(p):
        user = json.load(open(p, encoding="utf-8"))
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(b.get(k), dict): b[k].update(v)
            else: b[k] = v
    return b

BRAND = load_brand()

def _style():
    s = BRAND.get("style") or {}
    out = dict(STYLE_PRESETS.get(s.get("preset"), STYLE_PRESETS["handmade"]))
    for k, opts in STYLE_OPTIONS.items():
        if s.get(k) in opts: out[k] = s[k]
    return out

STYLE = _style()
if os.path.normcase(os.path.abspath(BRAND_DIR)) != os.path.normcase(os.path.join(HERE, "my-brand")):
    try: print(f"[reels_lib] channel: {BRAND['name']}  ({BRAND_DIR})")
    except UnicodeEncodeError: print(f"[reels_lib] channel: {BRAND_DIR!a}")

def _find_font(name):
    if os.path.isabs(name): return name if os.path.exists(name) else None
    for d in (os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
              os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"), BRAND_DIR, HERE):
        if os.path.exists(os.path.join(d, name)): return os.path.join(d, name)
    return None

sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # Chinese warnings on a cp950 console

def load_typeface(name, weight=400):
    """(typeface, label) for a font file name / path, or an installed family name (Windows lists most Chinese fonts
    by their local name, e.g. 微軟正黑體). Family names go through the system font manager, which also picks the
    right weight of variable fonts — loading those by file gives their default instance, often the thinnest."""
    path = _find_font(name)
    if path:
        tf = skia.Typeface.MakeFromFile(path)
        axes = tf.getVariationDesignParameters() if tf else []
        if any(a.tag == 0x77676874 and getattr(a, "def") < 350 for a in axes):   # 'wght' axis defaulting to Thin / Light
            print(f"[reels_lib] {os.path.basename(path)} is a variable font and loads very thin by file name; "
                  f"use its family name ({tf.getFamilyName()}) + font_weight in brand.json instead")
        return tf, path
    fm, style = skia.FontMgr.RefDefault(), skia.FontStyle(weight, 5, skia.FontStyle.kUpright_Slant)
    tf = fm.matchFamilyStyle(name, style)
    if tf is None:                           # some fonts register their name with a stray space (e.g. '小瀨字體 ')
        want = name.strip()
        for i in range(fm.countFamilies()):
            fam = fm.getFamilyName(i)
            if fam != name and fam.strip() == want:
                tf = fm.matchFamilyStyle(fam, style)
                if tf: break
    return tf, (f"{name} {weight}" if tf else None)

FONT, FONT_PATH = load_typeface(BRAND["font"], BRAND.get("font_weight", 400))
if FONT is None:
    print(f"[reels_lib] font {BRAND['font']} not found (python fonts.py list shows installed ones), using the default")
    FONT, FONT_PATH = load_typeface(BRAND_DEFAULTS["font"])
if FONT is None: sys.exit(f"Font {BRAND_DEFAULTS['font']} is not installed — run the Reels Studio installer.")

# ---------------- palette tokens (from brand.json; STYLE.md explains the roles) ----------------
_pal = dict(PALETTES.get(BRAND["palette"], PALETTES["cream"]), **BRAND.get("colors", {}))
BG = _pal["bg"]; INK = _pal["ink"]; ACC = _pal["accent"]; SUN = _pal["highlight"]; PEACH = _pal["peach"]; ROSE = _pal["rose"]
SAGE = _pal["sage"]; SKY = _pal["sky"]; LILAC = _pal["lilac"]; WHITE = "#FFFFFF"; GRAY = _pal["gray"]
RED = _pal["alert"]; GREEN = _pal["ok"]; COOL = "#E7ECEF"; MINT = "#CFE8E2"; STEEL = "#9AA9B5"

def mix(a, b, k):
    """hex colour k (0..1) of the way from a to b"""
    a, b = a.lstrip("#"), b.lstrip("#")
    return "#" + "".join(f"{round(int(a[i:i + 2], 16) * (1 - k) + int(b[i:i + 2], 16) * k):02X}" for i in (0, 2, 4))

# style "line": every INK outline (props, cards, frames) is drawn through P(), so it follows the channel's look
LINE_W = {"bold": 1.0, "thin": 0.55, "soft": 0.6}[STYLE["line"]]
LINE_INK = mix(INK, BG, 0.42) if STYLE["line"] == "soft" else INK
# style "motion": eback()'s overshoot (every pop-in, including the clip script's own) and transition length
MOTION_S = {"bouncy": 1.0, "snappy": 0.35, "gentle": 0.0}[STYLE["motion"]]

SAFE_TOP, SAFE_BOTTOM = 250, H - 250        # IG UI covers these; nothing important outside
SUB_Y = 1500                                 # subtitle box centre
ILLU_TOP, ILLU_BOTTOM = 380, 1300            # main illustration band

# ---------------- maths / easing ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def lerp(a, b, t): return a + (b - a) * t
def prog(t, t0, d): return clamp((t - t0) / d) if d > 0 else float(t >= t0)
def eo(x): return 1 - (1 - x) ** 3
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eback(x, s=1.70158):
    """ease-out with overshoot s, scaled by the style's motion (gentle = no overshoot, a plain ease-out)"""
    x = clamp(x)
    if x <= 0 or x >= 1: return x            # exact endpoints (formula gives ~2e-16 at 0, so `k > 0` checks misfire)
    s *= MOTION_S
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2

# ---------------- drawing primitives ----------------
def hx(h, a=1.0):
    h = h.lstrip("#")
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(clamp(a) * 255))

def P(color, a=1.0, stroke=0, blur=0, shader=None, dash=None, raw=False):
    """paint; an INK stroke is an outline and follows the style's line weight / colour (raw=True: exact as given)"""
    if stroke and not raw and color == INK and (LINE_W != 1.0 or LINE_INK != INK):
        stroke, color = max(2.0, stroke * LINE_W), LINE_INK
    p = skia.Paint(AntiAlias=True, Color=hx(color, a))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if shader: p.setShader(shader)
    if dash: p.setPathEffect(skia.DashPathEffect.Make(dash, 0))
    return p

def lin(x0, y0, x1, y1, cols):
    return skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [hx(c) for c in cols])

def rrect(c, x, y, w, h, r, paint): c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, paint)
def rect_path(x, y, w, h):
    p = skia.Path(); p.addRect(skia.Rect.MakeXYWH(x, y, w, h)); return p

class Xf:
    """with Xf(c, x, y, scale, rot_deg, alpha): draw in local coords (alpha<1 uses a layer)."""
    def __init__(s, c, x=0, y=0, sc=1.0, rot=0.0, alpha=1.0):
        s.c, s.x, s.y, s.sc, s.rot, s.a = c, x, y, sc, rot, alpha
    def __enter__(s):
        if s.a < 0.999: s.c.saveLayerAlpha(None, int(clamp(s.a) * 255))
        else: s.c.save()
        s.c.translate(s.x, s.y)
        if s.rot: s.c.rotate(s.rot)
        if s.sc != 1: s.c.scale(s.sc, s.sc)
        return s.c
    def __exit__(s, *a): s.c.restore()

def font(sz): return skia.Font(FONT, sz)

# ---------------- missing glyphs (they would render as blanks / boxes) ----------------
def missing_glyphs(s, tf=None):
    """characters of s the font cannot draw (whitespace and subtitle markup ignored)"""
    chars = sorted({ch for ch in s if not ch.isspace() and ch not in "【】|"})
    return [ch for ch, g in zip(chars, (tf or FONT).unicharsToGlyphs([ord(ch) for ch in chars])) if g == 0]

_SEEN, MISSING = set(), {}          # every drawn string is checked once; MISSING: char -> first text it was in
def _note(s):
    if s in _SEEN: return
    _SEEN.add(s)
    for ch in missing_glyphs(s): MISSING.setdefault(ch, s)

def glyph_warning(found, header):
    """found: {char: [where, ...]} -> printed warning block (nothing if empty)"""
    if not found: return
    fam = FONT.getFamilyName()
    print(f"\n⚠ {header}：字型「{fam}」沒有這些字，畫面上會變成空白或方框")
    for ch, where in found.items():
        print(f"   {ch}  (U+{ord(ch):04X})  " + "；".join(where[:3]))
    print("   處理：換成意思相同的字、拿掉 emoji，或換字型（python fonts.py check \"<字型>\" \"<文字>\" 可先測）。\n")

def fit(s, sz, maxw):
    """largest size <= sz at which s fits in maxw px (for brand names / tags of any length)"""
    w = font(sz).measureText(s)
    return sz if w <= maxw else max(24, int(sz * maxw / w))

def text(c, s, x, y, sz, color=INK, a=1.0, align="c", bold=0):
    _note(s)
    f = font(sz); w = f.measureText(s)
    xx = x - w / 2 if align == "c" else (x - w if align == "r" else x)
    if bold: c.drawString(s, xx, y, f, P(color, a, stroke=bold, raw=True))   # faux bold, not an outline
    c.drawString(s, xx, y, f, P(color, a))
    return w

def rich_line(c, s, cx, y, sz, base=INK, acc=ACC, a=1.0, hi=True, bold=2.2, outline=0):
    """「【關鍵字】」 segments get the accent colour + a mustard highlighter swipe.
    outline: width of a dark rim drawn behind the letters (outlined captions on any background)."""
    _note(s)
    parts, buf, on = [], "", False
    for ch in s:
        if ch in "【】":
            if buf: parts.append((buf, on))
            buf, on = "", ch == "【"
        else: buf += ch
    if buf: parts.append((buf, on))
    f = font(sz)
    x = cx - sum(f.measureText(p) for p, _ in parts) / 2
    for p, k in parts:
        w = f.measureText(p)
        if k and hi: rrect(c, x - 6, y - sz * 0.42, w + 12, sz * 0.5, sz * 0.18, P(SUN, 0.55 * a))
        col = acc if k else base
        if outline: c.drawString(p, x, y, f, P(INK, a, stroke=outline, raw=True))
        c.drawString(p, x, y, f, P(col, a, stroke=bold, raw=True)); c.drawString(p, x, y, f, P(col, a))
        x += w

def path_part(c, pth, k, paint):
    """draw the first k (0..1) of a path — for line-drawing animations"""
    if k <= 0.002: return                    # a zero-length segment with round caps would draw a dot
    m = skia.PathMeasure(pth, False); dst = skia.Path()
    m.getSegment(0, m.getLength() * clamp(k), dst, True); c.drawPath(dst, paint)

def shadow(c, x, y, w, h, r, a=0.18): rrect(c, x + 6, y + 14, w, h, r, P(INK, a, blur=18))

# ---------------- shared shapes ----------------
def star4(c, x, y, r, color, a=1.0):
    p = skia.Path(); p.moveTo(x, y - r)
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)): p.quadTo(x, y, x + dx * r, y + dy * r)
    p.close(); c.drawPath(p, P(color, a))

def star5(c, x, y, r, color, a=1.0, rot=0):
    p = skia.Path()
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45; ang = math.radians(rot - 90 + i * 36)
        (p.moveTo if i == 0 else p.lineTo)(x + rr * math.cos(ang), y + rr * math.sin(ang))
    p.close(); c.drawPath(p, P(color, a)); c.drawPath(p, P(INK, a * 0.9, stroke=5))

def blob(c, x, y, r, color, a, t, seed=0):
    p = skia.Path(); n = 8; pts = []
    for i in range(n):
        ang = i / n * 2 * math.pi
        rr = r * (1 + 0.08 * math.sin(t * 0.8 + i * 1.7 + seed) + 0.05 * math.cos(i * 2.3 + seed))
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    p.moveTo((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
    for i in range(n):
        a0, a1 = pts[(i + 1) % n], pts[(i + 2) % n]
        p.quadTo(a0[0], a0[1], (a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2)
    p.close(); c.drawPath(p, P(color, a))

def burst(c, r, col, n=14, rot=0):
    p = skia.Path()
    for i in range(n * 2):
        rr = r if i % 2 == 0 else r * 0.62; a = math.radians(rot + i * 180 / n)
        (p.moveTo if i == 0 else p.lineTo)(rr * math.cos(a), rr * math.sin(a))
    p.close(); c.drawPath(p, P(col)); c.drawPath(p, P(INK, stroke=8))

def heart(c, r, col, stroke=True):
    p = skia.Path(); p.moveTo(0, r * 0.9)
    p.cubicTo(-r * 1.6, -r * 0.2, -r * 0.7, -r * 1.3, 0, -r * 0.45)
    p.cubicTo(r * 0.7, -r * 1.3, r * 1.6, -r * 0.2, 0, r * 0.9); p.close()
    c.drawPath(p, P(col))
    if stroke: c.drawPath(p, P(INK, stroke=6))

def warning_sign(c, s=1.0):
    with Xf(c, 0, 0, s):
        tri = skia.Path(); tri.moveTo(0, -80); tri.lineTo(90, 70); tri.lineTo(-90, 70); tri.close()
        c.drawPath(tri, P(SUN)); c.drawPath(tri, P(INK, stroke=7)); text(c, "!", 0, 50, 100, INK, bold=3)

def stamp(c, s, col=RED, sz=96):
    w = font(sz).measureText(s) + 70
    rrect(c, -w / 2, -sz * 0.78, w, sz * 1.25, 22, P(col, stroke=10)); text(c, s, 0, sz * 0.32, sz, col, bold=2)

def xmark(c, x, y, r, k):
    p1 = skia.Path(); p1.moveTo(x - r, y - r); p1.lineTo(x + r, y + r)
    p2 = skia.Path(); p2.moveTo(x + r, y - r); p2.lineTo(x - r, y + r)
    path_part(c, p1, clamp(k * 2), P(RED, stroke=r * 0.32)); path_part(c, p2, clamp(k * 2 - 1), P(RED, stroke=r * 0.32))

def tick(c, x, y, r, k):
    c.drawCircle(x, y, r, P(GREEN)); c.drawCircle(x, y, r, P(INK, stroke=5))
    p = skia.Path(); p.moveTo(x - r * 0.45, y); p.lineTo(x - r * 0.1, y + r * 0.38); p.lineTo(x + r * 0.5, y - r * 0.35)
    path_part(c, p, k, P(WHITE, stroke=r * 0.24))

def gauge(c, r, val, label=None, shake=0.0, t=0):
    for i, col in enumerate((GREEN, SUN, RED)):
        p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(-r, -r, 2 * r, 2 * r), 180 + i * 60 + 2, 56); c.drawPath(p, P(col, stroke=r * 0.22))
    p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(-r * 1.14, -r * 1.14, 2.28 * r, 2.28 * r), 180, 180); c.drawPath(p, P(INK, stroke=6))
    ang = math.radians(180 + 180 * clamp(val + shake * math.sin(t * 40)))
    c.drawLine(0, 0, math.cos(ang) * r * 0.92, math.sin(ang) * r * 0.92, P(INK, stroke=12)); c.drawCircle(0, 0, r * 0.12, P(INK))
    if label: text(c, label, 0, r * 0.45, r * 0.3, INK)

def tape(c, w=260, txt=None):
    p = skia.Path(); p.moveTo(-w / 2, -38)
    for i in range(9): p.lineTo(-w / 2 + (i % 2) * 10, -38 + i * 9.5)
    p.lineTo(w / 2, 38)
    for i in range(9): p.lineTo(w / 2 - (i % 2) * 10, 38 - i * 9.5)
    p.close(); c.drawPath(p, P("#F3D9A4", 0.95)); c.drawPath(p, P(INK, 0.5, stroke=3))
    if txt: text(c, txt, 0, 14, 40, INK)

def sticky(c, s):
    shadow(c, -130, -110, 260, 220, 6, 0.2)
    rrect(c, -130, -110, 260, 220, 6, P("#FFE58A")); c.drawRect(skia.Rect.MakeXYWH(-130, -110, 260, 34), P("#F7D25F"))
    text(c, s, 0, 40, 64, INK, bold=1.5)

def flower(c, col, t):
    c.drawLine(0, 0, 0, 120, P("#6FA77A", stroke=8))
    for i in range(6):
        a = math.radians(i * 60 + t * 20); c.drawCircle(30 * math.cos(a), 30 * math.sin(a), 26, P(col))
    c.drawCircle(0, 0, 22, P(SUN)); c.drawCircle(0, 0, 22, P(INK, stroke=4))

def mic(c):
    c.drawLine(0, 120, 0, 210, P(INK, stroke=14)); rrect(c, -70, 205, 140, 22, 11, P(INK))
    p = skia.Path(); p.addArc(skia.Rect.MakeXYWH(-95, -20, 190, 160), 0, 180); c.drawPath(p, P(INK, stroke=12))
    rrect(c, -62, -150, 124, 250, 62, P(ACC)); rrect(c, -62, -150, 124, 250, 62, P(INK, stroke=6))
    for i in range(5): c.drawLine(-40, -110 + i * 26, 40, -110 + i * 26, P(WHITE, 0.6, stroke=6))

# ---------------- consistent background + decoration layer ----------------
SPARKS = [(80, 420, 22, SUN), (1000, 520, 18, ACC), (60, 1180, 16, ROSE), (1015, 1120, 24, SUN),
          (140, 760, 12, ACC), (950, 860, 14, SAGE), (900, 330, 12, ROSE), (190, 330, 10, SAGE)]

def deco(c, t, a=1.0):
    """the channel's decoration layer (style "background"): sparkles + rings / none / a few pencil marks / soft glints"""
    bgs = STYLE["background"]
    if bgs == "plain": return
    if bgs == "blobs":
        for i, (x, y, r, col) in enumerate(SPARKS):
            star4(c, x, y + 6 * math.sin(t * 1.4 + i), r * (0.65 + 0.35 * math.sin(t * 2.6 + i * 1.3)), col, a)
        for i, (x, y) in enumerate([(110, 1010), (980, 980), (930, 420)]):
            c.drawCircle(x, y + 5 * math.sin(t * 2 + i), 9, P(INK, 0.25 * a, stroke=4))
    elif bgs == "grid":                      # doodles in the notebook margin
        for i, (x, y) in enumerate([(48, 470), (48, 1080)]):
            star4(c, x, y + 4 * math.sin(t * 1.4 + i), 15, ACC, 0.55 * a)
        c.drawCircle(1000, 430 + 4 * math.sin(t * 2), 12, P(INK, 0.22 * a, stroke=3))
    else:                                    # gradient: a few faint glints
        for i, (x, y, r) in enumerate([(130, 460, 16), (960, 820, 20), (900, 1210, 12)]):
            star4(c, x, y + 5 * math.sin(t * 1.4 + i), r * (0.7 + 0.3 * math.sin(t * 2.6 + i)), WHITE, 0.85 * a)

def paper_bg(c, t, base=BG):
    """the channel's background (style "background"); base: the paper colour, e.g. SKY for a contrasting scene"""
    bgs = STYLE["background"]
    c.drawColor(hx(base))
    if bgs == "blobs":
        blob(c, -40, 300, 300, PEACH, 0.45, t, 1); blob(c, 1120, 1500, 340, SUN, 0.22, t, 2)
        blob(c, 1100, 250, 180, SAGE, 0.25, t, 3); blob(c, -60, 1650, 220, ROSE, 0.2, t, 4)
    elif bgs == "grid":
        line = P(INK, 0.07, stroke=2, raw=True)
        for x in range(30, W, 60): c.drawLine(x, 0, x, H, line)
        for y in range(30, H, 60): c.drawLine(0, y, W, y, line)
        c.drawLine(96, 0, 96, H, P(ROSE, 0.45, stroke=3, raw=True))           # margin line
    elif bgs == "gradient":
        c.drawPaint(P(base, shader=lin(0, 0, 0, H, [mix(base, WHITE, 0.5), mix(base, PEACH, 0.4)])))
        for x, y, r, col, a in ((860 + 30 * math.sin(t * 0.4), 520, 520, SUN, 0.30), (180, 1450 + 30 * math.cos(t * 0.35), 560, SKY, 0.26)):
            c.drawCircle(x, y, r, P(col, shader=skia.GradientShader.MakeRadial(skia.Point(x, y), r, [hx(col, a), hx(col, 0)])))

def cool_bg(c, t):
    """hospital / low-mood variant of paper_bg — same blobs, cooler colours"""
    c.drawPaint(P(BG, shader=lin(0, 0, 0, H, [COOL, "#F4F2EF"])))
    blob(c, -40, 320, 280, MINT, 0.6, t, 1); blob(c, 1120, 1500, 320, "#DCE3EA", 0.7, t, 2)
    deco(c, t, 0.45)

def gradient_bg(c, top, bottom):
    c.drawPaint(P(BG, shader=lin(0, 0, 0, H, [top, bottom])))

# ---------------- stock media (Pexels photos / videos) ----------------
_IMG, _VID = {}, {}

def load_image(path):
    # MakeFromEncoded does not copy the bytes; once the temp buffer is freed the photo can decode as flat grey.
    # Copy into skia.Data and decode eagerly so the image owns its pixels.
    if path not in _IMG:
        img = skia.Image.MakeFromEncoded(skia.Data.MakeWithCopy(open(path, "rb").read()))
        _IMG[path] = img.makeRasterImage() if img is not None else None
    return _IMG[path]

class VideoSource:
    """Frame-accurate reader for a stock clip or the speaker's own footage. Frames are scaled so the short side
    is ~1080 px (enough for full-bleed) to keep memory and decode time down.
    loop=True (stock B-roll): frame_at(sec) wraps past the end.  loop=False (source footage): clamps.
    rotate: None = follow the file's display matrix (phone videos shot upright are stored sideways + a rotation
    tag); 0 / 90 / -90 / 180 forces a counter-clockwise rotation when a file is tagged wrong."""
    def __init__(s, path, loop=True, rotate=None):
        s.c = av.open(path); s.st = s.c.streams.video[0]; s.st.thread_type = "AUTO"
        s.loop, s.rotate = loop, rotate
        s.dur = float(s.st.duration * s.st.time_base) if s.st.duration else s.c.duration / 1e6
        s.t_first = float(s.st.start_time * s.st.time_base) if s.st.start_time is not None else 0.0
        w, h = s.st.codec_context.width, s.st.codec_context.height
        k = min(1.0, 1080 / min(w, h)); s.tw, s.th = int(w * k) // 2 * 2, int(h * k) // 2 * 2
        s.it, s.cur_t, s.img, s.pending = None, -1e9, None, None
    def _seek(s, t):
        s.c.seek(int(max(0, t - 0.05) / s.st.time_base), stream=s.st, backward=True)
        s.it = s.c.decode(s.st); s.cur_t, s.img, s.pending = -1e9, None, None
    def _image(s, f):
        a = f.to_ndarray(format="rgba", width=s.tw, height=s.th)
        rot = s.rotate if s.rotate is not None else (getattr(f, "rotation", 0) or 0)
        q = int(round(rot / 90)) % 4                      # display matrix angle is counter-clockwise, like rot90
        if q: a = np.ascontiguousarray(np.rot90(a, q))
        return skia.Image.fromarray(a, colorType=skia.kRGBA_8888_ColorType)
    def frame_at(s, t):
        if s.loop: t = t % max(0.1, s.dur - 0.1)
        else: t = clamp(t, s.t_first, s.t_first + s.dur - 0.05)
        if s.it is None or t < s.cur_t - 1e-3 or t > s.cur_t + 1.0: s._seek(t)
        while True:
            f = s.pending or next(s.it, None); s.pending = None
            if f is None: break
            ft = float(f.pts * s.st.time_base) if f.pts is not None else s.cur_t + 1 / 30
            if ft > t + 1e-3 and s.img is not None:
                s.pending = f; break                       # keep it for the next call
            s.cur_t = ft
            s.img = s._image(f)
            if ft >= t - 1e-3: break
        return s.img

def video(path, loop=True, rotate=None):
    key = (path, loop, rotate)
    if key not in _VID: _VID[key] = VideoSource(path, loop, rotate)
    return _VID[key]

GRADES = {  # colour grade overlays (soft-light) so stock media sits closer to the palette; None = original colour
    "warm": (SUN, 0.35), "peach": (PEACH, 0.45), "cool": (SKY, 0.40), "fade": (BG, 0.35),
}

def draw_media(c, img, rect=(0, 0, W, H), radius=0, zoom=(1.0, 1.08), pan=((0, 0), (0, -40)), k=0.0,
               grade=None, alpha=1.0, card=False, focus=(0.5, 0.5)):
    """Draw a photo/video frame cover-fitted into rect with a Ken Burns move (k: 0..1 progress through the shot).
    focus: point of the image (0..1, 0..1) kept as close to the rect centre as the crop allows — e.g. where the
    speaker's face is in a landscape shot.
    card=True: white border + shadow + ink outline (polaroid look that matches the illustrations)."""
    if img is None: return
    x, y, w, h = rect
    if card:
        shadow(c, x - 18, y - 18, w + 36, h + 36, radius + 10, 0.22)
        rrect(c, x - 18, y - 18, w + 36, h + 36, radius + 10, P(WHITE)); rrect(c, x - 18, y - 18, w + 36, h + 36, radius + 10, P(INK, stroke=6))
    c.save()
    if radius: c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), radius, radius), True)
    else: c.clipRect(skia.Rect.MakeXYWH(x, y, w, h))
    sc = lerp(zoom[0], zoom[1], k); dx = lerp(pan[0][0], pan[1][0], k); dy = lerp(pan[0][1], pan[1][1], k)
    iw, ih = img.width(), img.height(); s = max(w / iw, h / ih) * sc; dw, dh = iw * s, ih * s
    x0 = clamp(x + w / 2 - focus[0] * dw, x + w - dw, x); y0 = clamp(y + h / 2 - focus[1] * dh, y + h - dh, y)
    dst = skia.Rect.MakeXYWH(x0 + dx, y0 + dy, dw, dh)
    c.drawImageRect(img, dst, skia.SamplingOptions(skia.FilterMode.kLinear), skia.Paint(Alphaf=alpha))
    if grade:
        col, amt = GRADES[grade]
        gp = P(col, amt); gp.setBlendMode(skia.BlendMode.kSoftLight); c.drawRect(skia.Rect.MakeXYWH(x, y, w, h), gp)
    c.restore()

def photo_scene(c, path, lt, dur, grade=None, **kw):
    """full-bleed photo B-roll with Ken Burns over the scene duration"""
    draw_media(c, load_image(path), k=eio(prog(lt, 0, dur)), grade=grade, **kw)

def video_scene(c, path, lt, dur, offset=0.0, grade=None, **kw):
    """full-bleed stock video B-roll; offset = where in the stock clip to start"""
    draw_media(c, video(path).frame_at(offset + lt), k=eio(prog(lt, 0, dur)), grade=grade,
               zoom=kw.pop("zoom", (1.0, 1.04)), pan=kw.pop("pan", ((0, 0), (0, 0))), **kw)

# ---------------- edit decision list ----------------
class Timeline:
    """KEEPS = [(src_start, src_end), ...] in EPISODE seconds.  o(src) -> output second."""
    def __init__(s, keeps, seg_t0, lead=0.35, end_hold=0.4, end_card=3.6):
        s.KEEPS, s.SEG_T0, s.LEAD = keeps, seg_t0, lead
        s.SPEECH_END = s.o(keeps[-1][1])
        s.END_START = s.SPEECH_END + end_hold
        s.TOTAL = s.END_START + end_card
    def o(s, src):
        acc = s.LEAD
        for a, b in s.KEEPS:
            if src < a: return acc
            if src <= b: return acc + (src - a)
            acc += b - a
        return acc
    def src(s, out):
        """inverse of o(): source second shown at output second `out` (holds the first / last frame outside speech)"""
        acc = s.LEAD
        for a, b in s.KEEPS:
            if out < acc + (b - a): return a + max(0.0, out - acc)
            acc += b - a
        return s.KEEPS[-1][1]
    def keep_index(s, out):
        """which KEEPS range is playing at output second `out` (changes at every jump cut)"""
        acc = s.LEAD
        for i, (a, b) in enumerate(s.KEEPS):
            acc += b - a
            if out < acc: return i
        return len(s.KEEPS) - 1

def build_audio(tl, seg_wav, out_wav, tail_fade=0.08, target_db=-17):
    a, sr = sf.read(seg_wav)
    if a.ndim == 1: a = np.stack([a, a], 1)
    rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
    for s0, s1 in tl.KEEPS:
        for t in (s0, s1):
            i = int((t - tl.SEG_T0) * sr); v = rms(a[max(0, i - 480): i + 480])
            print(f"cut {t:8.2f}: {v:6.1f} dB {'OK' if v < -32 else '<-- LOUD: move into a silence'}")
    XF = int(0.012 * sr); out = np.zeros((int(tl.LEAD * sr), 2))
    for s0, s1 in tl.KEEPS:
        piece = a[int((s0 - tl.SEG_T0) * sr): int((s1 - tl.SEG_T0) * sr)].copy()
        ramp = np.linspace(0, 1, XF)[:, None]; piece[:XF] *= ramp; piece[-XF:] *= ramp[::-1]
        out = np.concatenate([out, piece])
    f = int(tail_fade * sr); out[-f:] *= np.linspace(1, 0, f)[:, None]
    n = int(tl.TOTAL * sr); out = np.concatenate([out, np.zeros((max(0, n - len(out)) + sr // 10, 2))])[:n]
    out *= 10 ** ((target_db - rms(out[out.any(axis=1)])) / 20)
    out = np.tanh(out / 0.89) * 0.89
    sf.write(out_wav, out.astype(np.float32), sr)
    print(f"audio {len(out) / sr:.2f}s peak {np.abs(out).max():.2f} -> {out_wav}")

# ---------------- subtitles / overlays ----------------
def draw_subtitle(c, t, s, t0, who="r"):
    """s: lines split by '|', keywords in 【】, leading '!' = punch card (bigger, red, tilted).
    who: 'r' main speaker (dark border) / 'h' second speaker (sage border + brand speaker_label chip, 「主持人」 by
    default) / any other string = sage border + that string as the chip, e.g. 'Amy'."""
    big = s.startswith("!"); s = s.lstrip("!")
    k = eback(prog(t, t0, 0.3 if big else 0.22), 3.0 if big else 2.2)
    lines = s.split("|")
    sz, lh = (130, 150) if big else (82, 108)
    f = font(sz)
    wmax = max(f.measureText(l.replace("【", "").replace("】", "")) for l in lines)
    bw, bh = wmax + 90, lh * len(lines) + 46
    chip = None if who == "r" else (BRAND["speaker_label"] if who == "h" else who)
    edge = SAGE if chip else INK
    st = STYLE["subtitle"]
    y0 = -bh / 2 + 23 + lh * 0.72
    with Xf(c, W / 2, SUB_Y, lerp(0.5 if big else 0.86, 1, k), -3 if big else 0, clamp(prog(t, t0, 0.12) * 1.2)):
        if st == "box":                      # white framed box (original)
            shadow(c, -bw / 2, -bh / 2, bw, bh, 36, 0.16)
            rrect(c, -bw / 2, -bh / 2, bw, bh, 36, P(WHITE, 0.94))
            rrect(c, -bw / 2, -bh / 2, bw, bh, 36, P(edge, 0.95, stroke=6 if chip else 5))
        elif st == "dark":                   # dark translucent box, light text; a second speaker gets a sage rim
            rrect(c, -bw / 2, -bh / 2, bw, bh, 28, P(INK, 0.86))
            if chip: rrect(c, -bw / 2, -bh / 2, bw, bh, 28, P(SAGE, stroke=5, raw=True))
        elif st == "pill":                   # one white pill per line, sticker-like
            ph = min(sz * 1.2, lh - 8)
            for i, l in enumerate(lines):
                lw = f.measureText(l.replace("【", "").replace("】", ""))
                yy = y0 + i * lh - sz * 0.86
                shadow(c, -lw / 2 - 32, yy, lw + 64, ph, ph / 2, 0.12)
                rrect(c, -lw / 2 - 32, yy, lw + 64, ph, ph / 2, P(WHITE, 0.96))
                if chip: rrect(c, -lw / 2 - 32, yy, lw + 64, ph, ph / 2, P(SAGE, stroke=5, raw=True))
        # outline: nothing behind the letters
        if chip:
            cw = font(32).measureText(chip) + 36
            with Xf(c, -bw / 2 + 20, -bh / 2 - 6):
                rrect(c, 0, -26, cw, 50, 25, P(SAGE)); rrect(c, 0, -26, cw, 50, 25, P(INK, 0.8, stroke=3))
                text(c, chip, cw / 2, 12, 32, INK)
        for i, l in enumerate(lines):
            if st == "dark": rich_line(c, l, 0, y0 + i * lh, sz, base=WHITE, acc=SUN, hi=False)
            elif st == "outline": rich_line(c, l, 0, y0 + i * lh, sz, base=WHITE, acc=SUN, hi=False, outline=sz * 0.13)
            else: rich_line(c, l, 0, y0 + i * lh, sz, acc=RED if big else ACC)

def top_tag(c, t, label):
    with Xf(c, W / 2, 318):
        sz = fit(label, 36, 860); w = font(sz).measureText(label)
        rrect(c, -w / 2 - 30, -38, w + 60, 64, 32, P(WHITE, 0.88)); rrect(c, -w / 2 - 30, -38, w + 60, 64, 32, P(INK, 0.6, stroke=3))
        c.drawCircle(-w / 2 - 6, -6, 8, P(ACC, 0.6 + 0.4 * math.sin(t * 5)))
        text(c, label, 8, 6, sz, INK)

def title_card(c, t, lt, rows, punch, punch_bg=SUN, y=790, bg=None):
    """Hook card for 0-3 s. rows: ≤3 rich-text lines (92px); punch: big accent line (≤6 chars ideal).
    bg: optional fn(c) drawn instead of the paper background — e.g. lambda c: R.face(c, t) so the speaker is
    already on screen behind the card (a light wash keeps the card readable)."""
    if bg:
        bg(c); c.drawRect(skia.Rect.MakeXYWH(0, 0, W, H), P(BG, 0.35))
    else:
        paper_bg(c, t); deco(c, t)
    k = eback(prog(lt, 0.0, 0.45), 1.4)
    style = STYLE["title"]
    if style != "note": return _title_styled(c, t, lt, rows, punch, punch_bg, y, k, style)
    with Xf(c, W / 2, y, lerp(0.4, 1, k), lerp(-14, -3, k) + 1.2 * math.sin(t * 2)):
        shadow(c, -420, -330, 840, 660, 40, 0.2)
        rrect(c, -420, -330, 840, 660, 40, P(WHITE)); rrect(c, -420, -330, 840, 660, 40, P(INK, stroke=6))
        for x, r in ((-260, -8), (260, 7)):
            with Xf(c, x, -330, 1, r): rrect(c, -80, -26, 160, 52, 6, P(SUN, 0.75))
        n = len(rows); y0 = -175 if n == 3 else -120
        for i, s in enumerate(rows):
            kk = eback(prog(lt, 0.12 + i * 0.16, 0.3))
            with Xf(c, 0, y0 + i * 118, lerp(0.3, 1, kk), 0, clamp(kk * 1.5)): rich_line(c, s, 0, 30, 92, bold=2.5)
        kk = eback(prog(lt, 0.7, 0.4), 2.5)
        shake = 6 * math.sin(lt * 40) * prog(lt, 1.3, 0.1) * (1 - prog(lt, 1.7, 0.2))
        f = font(130); w = f.measureText(punch)
        with Xf(c, shake, 225, lerp(0.2, 1, kk), -4, clamp(kk * 1.5)):
            rrect(c, -w / 2 - 40, -66, w + 80, 96, 30, P(punch_bg, 0.55)); text(c, punch, 0, 18, 130, ACC, bold=4)

def _plain(s): return s.replace("【", "").replace("】", "")

def _title_rows(c, lt, rows, y_first, step, sz, maxw, **kw):
    """the hook rows, popping in one after another, each shrunk to fit maxw"""
    for i, s in enumerate(rows):
        kk = eback(prog(lt, 0.12 + i * 0.16, 0.3))
        size = fit(_plain(s), sz, maxw)
        with Xf(c, 0, y_first + i * step, lerp(0.3, 1, kk), 0, clamp(kk * 1.5)): rich_line(c, s, 0, 30, size, **kw)

def _title_styled(c, t, lt, rows, punch, punch_bg, y, k, style):
    """title_card for the bold / line / magazine looks (note is drawn inline in title_card)"""
    n = len(rows)
    kk = eback(prog(lt, 0.7, 0.4), 2.5)
    shake = 6 * math.sin(lt * 40) * prog(lt, 1.3, 0.1) * (1 - prog(lt, 1.7, 0.2))
    if style == "bold":                      # no card: big outlined words straight on the background
        with Xf(c, W / 2, y, lerp(0.6, 1, k)):
            _title_rows(c, lt, rows, -250 if n == 3 else -180, 132, 108, 960, bold=3, outline=10, base=WHITE, acc=SUN, hi=False)
            sz = fit(punch, 180, 940); w = font(sz).measureText(punch)
            with Xf(c, shake, 250, lerp(0.2, 1, kk), -5, clamp(kk * 1.5)):
                rrect(c, -w / 2 - 44, -sz * 0.72, w + 88, sz * 0.98, 24, P(ACC))
                text(c, punch, 0, sz * 0.12, sz, WHITE, bold=4)
    elif style == "line":                    # quiet card: thin frame, accent bar, underlined punch line
        with Xf(c, W / 2, y, lerp(0.92, 1, k), 0, clamp(k * 1.4)):
            shadow(c, -420, -330, 840, 660, 10, 0.08)
            rrect(c, -420, -330, 840, 660, 10, P(WHITE, 0.97)); rrect(c, -420, -330, 840, 660, 10, P(INK, 0.85, stroke=3, raw=True))
            c.drawRect(skia.Rect.MakeXYWH(-420, -330, 14, 660), P(ACC))
            label = BRAND["tag"] or BRAND["name"]
            text(c, label, -370, -262, fit(label, 34, 700), ACC, align="l")
            _title_rows(c, lt, rows, -175 if n == 3 else -120, 112, 88, 740, hi=False, bold=2)
            sz = fit(punch, 120, 720); w = font(sz).measureText(punch)
            with Xf(c, shake, 228, lerp(0.6, 1, kk), 0, clamp(kk * 1.5)):
                text(c, punch, 0, 10, sz, ACC, bold=3)
                rrect(c, -w / 2, 34, w * eo(prog(lt, 0.9, 0.35)), 12, 6, P(SUN))
    else:                                    # magazine: a tilted colour slab sliding in, white type, punch on a label
        slide = (1 - eo(prog(lt, 0.0, 0.4))) * -W
        with Xf(c, W / 2 + slide, y, 1, -5):
            c.drawRect(skia.Rect.MakeXYWH(-W * 0.8, -330, W * 1.6, 660), P(ACC))
            c.drawRect(skia.Rect.MakeXYWH(-W * 0.8, 318, W * 1.6, 14), P(SUN))
            label = BRAND["tag"] or BRAND["name"]
            text(c, label, -440, -262, fit(label, 34, 800), WHITE, a=0.85, align="l")
            _title_rows(c, lt, rows, -165 if n == 3 else -110, 116, 96, 900, base=WHITE, acc=SUN, hi=False, bold=3)
            sz = fit(punch, 124, 820); w = font(sz).measureText(punch)
            with Xf(c, shake, 240, lerp(0.5, 1, kk), 3, clamp(kk * 1.5)):
                rrect(c, -w / 2 - 36, -sz * 0.7, w + 72, sz * 0.96, 8, P(punch_bg))
                text(c, punch, 0, sz * 0.12, sz, INK, bold=3)

def play_button(c):
    shadow(c, -170, -170, 340, 340, 170, 0.2)
    c.drawCircle(0, 0, 170, P(ACC)); c.drawCircle(0, 0, 170, P(INK, stroke=8))
    tri = skia.Path(); tri.moveTo(-50, -80); tri.lineTo(-50, 80); tri.lineTo(85, 0); tri.close()
    c.drawPath(tri, P(WHITE)); c.drawPath(tri, P(INK, stroke=6))

LOGO_PATH = os.path.join(BRAND_DIR, "logo.png")   # uploaded in the panel (結尾卡 → 圖示 → 我的 logo)

def brand_logo(c, size=360):
    """the channel's own logo, centred on the origin like the other end-card icons.
    end_card.logo_shape: circle (cropped to a circle) | rounded (rounded square) | original (as is, keeps transparency)"""
    img = load_image(LOGO_PATH) if os.path.exists(LOGO_PATH) else None
    if img is None:
        print("[reels_lib] end_card.icon is 'logo' but there is no logo.png in the channel folder; using the play icon")
        return play_button(c)
    shape = BRAND["end_card"].get("logo_shape", "original")
    w, h = img.width(), img.height()
    if shape == "original":                  # fit inside the box, keep its own outline
        k = size / max(w, h); dw, dh = w * k, h * k
        c.drawImageRect(img, skia.Rect.MakeXYWH(-dw / 2, -dh / 2, dw, dh), skia.SamplingOptions(skia.FilterMode.kLinear))
        return
    k = size / min(w, h); dw, dh = w * k, h * k  # fill the shape, crop the overflow
    clip = skia.Path()
    if shape == "circle": clip.addCircle(0, 0, size / 2)
    else: clip.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-size / 2, -size / 2, size, size), size * 0.22, size * 0.22))
    shadow(c, -size / 2, -size / 2, size, size, size / 2 if shape == "circle" else size * 0.22, 0.18)
    c.save(); c.clipPath(clip, skia.ClipOp.kIntersect, True)
    c.drawColor(hx(WHITE))
    c.drawImageRect(img, skia.Rect.MakeXYWH(-dw / 2, -dh / 2, dw, dh), skia.SamplingOptions(skia.FilterMode.kLinear))
    c.restore()
    c.drawPath(clip, P(INK, stroke=6))

END_ICONS = {"mic": mic, "play": play_button, "heart": lambda c: heart(c, 150, ACC),
             "star": lambda c: star5(c, 0, 0, 190, SUN), "logo": brand_logo, "none": None}

def end_card(c, t, lt, show=None, guest=None, cta=None, sub=None, ep=None, icon=None, badge=None):
    """Brand end card; every argument left as None comes from brand.json → end_card.
    guest + ep: ep='EP79' -> the line under the name reads 「EP79｜Amy」 instead of 「本集來賓｜Amy」."""
    e = BRAND["end_card"]
    show = show or BRAND["name"]; cta = cta or e["cta"]; sub = e["sub"] if sub is None else sub
    badge = e["badge"] if badge is None else badge; draw_icon = END_ICONS.get(icon or e["icon"], mic)
    paper_bg(c, t); deco(c, t)
    line = f"{ep}｜{guest}" if ep and guest else (ep or (f"{e['guest_prefix']}｜{guest}" if guest else None))
    if STYLE["end"] != "classic": return _end_styled(c, t, lt, show, line, bool(ep), cta, sub, badge, draw_icon, STYLE["end"])
    k = eback(prog(lt, 0, 0.5), 1.6)
    if draw_icon:
        for i in range(3):
            ph = (lt * 0.7 + i / 3) % 1; c.drawCircle(540, 640, 120 + ph * 260, P(ACC, (1 - ph) * 0.5, stroke=8))
        with Xf(c, 540, 640, 0.95 * k, 6 * math.sin(t * 2)): draw_icon(c)
    if badge:
        bw = max(300, font(130).measureText(badge) + 40)
        with Xf(c, 540, 1060, eback(prog(lt, 0.2, 0.45), 1.8), -3):
            rrect(c, -bw / 2, -90, bw, 120, 30, P(SUN, 0.55)); text(c, badge, 0, 5, 130, ACC, bold=4)
    kt2 = eo(prog(lt, 0.35, 0.4))
    with Xf(c, 540, 1180 + (1 - kt2) * 40, 1, 0, kt2):
        text(c, show, 0, 0, fit(show, 96, 940), INK, bold=2.5)
        if line: text(c, line, 0, 80, fit(line, 48 if ep else 44, 900), INK, a=0.8 if ep else 0.7, bold=1 if ep else 0)
    with Xf(c, 540, 1440, eback(prog(lt, 0.6, 0.45), 2.2) * (1 + 0.04 * math.sin(t * 6))):
        sz = fit(cta, 76, 400); tw = font(sz).measureText(cta); bw = max(560, tw + 220)
        shadow(c, -bw / 2, -70, bw, 140, 70, 0.22)
        rrect(c, -bw / 2, -70, bw, 140, 70, P(ACC)); rrect(c, -bw / 2, -70, bw, 140, 70, P(INK, stroke=6))
        tri = skia.Path(); tri.moveTo(-bw / 2 + 90, -32); tri.lineTo(-bw / 2 + 90, 32); tri.lineTo(-bw / 2 + 145, 0); tri.close()
        c.drawPath(tri, P(WHITE))
        text(c, cta, max(-bw / 2 + 320, -bw / 2 + 160 + tw / 2), 26, sz, WHITE, bold=2.5)   # clear of the ▶
    if sub:
        with Xf(c, 540, 1590, 1, 0, eo(prog(lt, 0.9, 0.4))): text(c, sub, 0, 0, fit(sub, 44, 900), INK, a=0.75)

def _cta(c, cta, filled=True, width=560):
    """the call-to-action button: filled accent pill with a ▶, or an accent outline"""
    sz = fit(cta, 72, 400); tw = font(sz).measureText(cta); bw = max(width, tw + 220)
    if filled:
        shadow(c, -bw / 2, -66, bw, 132, 66, 0.18)
        rrect(c, -bw / 2, -66, bw, 132, 66, P(ACC)); rrect(c, -bw / 2, -66, bw, 132, 66, P(INK, stroke=6))
    else:
        rrect(c, -bw / 2, -66, bw, 132, 66, P(WHITE, 0.7)); rrect(c, -bw / 2, -66, bw, 132, 66, P(ACC, stroke=5, raw=True))
    col = WHITE if filled else ACC
    tri = skia.Path(); tri.moveTo(-bw / 2 + 90, -30); tri.lineTo(-bw / 2 + 90, 30); tri.lineTo(-bw / 2 + 142, 0); tri.close()
    c.drawPath(tri, P(col))
    text(c, cta, max(-bw / 2 + 320, -bw / 2 + 160 + tw / 2), 25, sz, col, bold=2.5)

def _end_styled(c, t, lt, show, line, is_ep, cta, sub, badge, draw_icon, style):
    """end_card for the minimal / card looks (classic is drawn inline in end_card)"""
    k = eback(prog(lt, 0, 0.5), 1.6)
    kt2 = eo(prog(lt, 0.35, 0.4))
    if style == "minimal":                   # small icon, big name, a thin rule, outlined button
        if draw_icon:                        # a logo is the point of the card, a stock icon is decoration
            with Xf(c, 540, 700, (0.85 if draw_icon is brand_logo else 0.55) * k): draw_icon(c)
        if badge:
            with Xf(c, 540, 930, 1, 0, eo(prog(lt, 0.2, 0.4))): text(c, badge, 0, 0, fit(badge, 64, 700), ACC, bold=2)
        with Xf(c, 540, 1090 + (1 - kt2) * 30, 1, 0, kt2):
            text(c, show, 0, 0, fit(show, 104, 940), INK, bold=2.5)
            if line: text(c, line, 0, 76, fit(line, 44, 900), INK, a=0.75)
        rw = 300 * eo(prog(lt, 0.5, 0.4))
        c.drawLine(540 - rw, 1215, 540 + rw, 1215, P(INK, 0.35, stroke=3, raw=True))
        with Xf(c, 540, 1370, lerp(0.85, 1, eback(prog(lt, 0.6, 0.4))), 0, eo(prog(lt, 0.6, 0.3))): _cta(c, cta, filled=False)
        if sub:
            with Xf(c, 540, 1530, 1, 0, eo(prog(lt, 0.9, 0.4))): text(c, sub, 0, 0, fit(sub, 42, 900), INK, a=0.7)
    else:                                    # card: everything on one profile-style card
        with Xf(c, 540, 985, lerp(0.85, 1, k), 0, clamp(k * 1.5)):
            shadow(c, -390, -470, 780, 880, 48, 0.16)
            rrect(c, -390, -470, 780, 880, 48, P(WHITE, 0.97)); rrect(c, -390, -470, 780, 880, 48, P(INK, stroke=5))
            c.drawCircle(0, -255, 165, P(SUN, 0.45))
            if draw_icon:
                with Xf(c, 0, -255, 0.6): draw_icon(c)
            if badge:
                with Xf(c, 250, -410, eback(prog(lt, 0.2, 0.45), 1.8), 8):
                    bw = font(64).measureText(badge) + 44
                    rrect(c, -bw / 2, -50, bw, 80, 40, P(ACC)); text(c, badge, 0, 12, fit(badge, 52, 240), WHITE, bold=2)
            with Xf(c, 0, 30 + (1 - kt2) * 30, 1, 0, kt2):
                text(c, show, 0, 0, fit(show, 92, 700), INK, bold=2.5)
                if line: text(c, line, 0, 72, fit(line, 44 if is_ep else 40, 700), INK, a=0.75)
            with Xf(c, 0, 262, eback(prog(lt, 0.6, 0.45), 2.0)): _cta(c, cta, width=520)
        if sub:
            with Xf(c, 540, 1475, 1, 0, eo(prog(lt, 0.9, 0.4))): text(c, sub, 0, 0, fit(sub, 42, 900), INK, a=0.75)

# ---------------- the reel ----------------
class Reel:
    """scenes: [(name, out_start_sec, fn(c, t, lt, dur))], first must start at 0 (title card), last = end card.
    subs:   [(text, SOURCE second, who)]  — converted with timeline.o().
    trans:  {scene_name: 'circle' | 'slide' | 'zoom' | 'cut'}  transition INTO that scene.
    source_video: the speaker's own recording (same file words.py read, so its clock = SOURCE seconds) for R.face().
    rotate: force the source footage rotation if the file's tag is wrong (see VideoSource)."""
    TR = {"bouncy": 0.32, "snappy": 0.24, "gentle": 0.45}[STYLE["motion"]]

    def __init__(s, clipdir, out_mp4, timeline, subs, scenes, trans, tag=None, hide_tag=("title", "end"),
                 source_video=None, rotate=None):
        s.dir, s.out, s.tl, s.trans, s.hide_tag = clipdir, out_mp4, timeline, trans, hide_tag
        s.tag = tag or BRAND["tag"] or BRAND["name"]
        s.src_video, s.rotate = source_video, rotate
        s.scenes = scenes
        s.start = {n: st for n, st, _ in scenes}
        s.subs = [(txt, timeline.o(src), who) for txt, src, who in subs]
        for txt, _, _ in subs:
            for line in txt.lstrip("!").split("|"):
                n = len(line.replace("【", "").replace("】", ""))
                assert n <= 12, f"subtitle line over 12 chars ({n}): {line}"
        assert scenes[0][1] == 0.0
        s.reported = s.check_glyphs(subs)

    def check_glyphs(s, subs):
        """Warn before anything is rendered about characters the brand font lacks: in the subtitles, the brand
        texts, and every string literal of the clip script (title rows, stamps, labels ...). Returns the chars."""
        found = {}
        def add(where, txt):
            if isinstance(txt, str):
                for ch in missing_glyphs(txt.lstrip("!")): found.setdefault(ch, []).append(f"{where}「{txt[:20]}」")
        for txt, src, _ in subs: add(f"字幕 {src:.1f}s", txt)
        e = BRAND["end_card"]
        for k, v in (("頂部標籤", s.tag), ("頻道名稱", BRAND["name"]), ("結尾按鈕", e["cta"]), ("結尾小字", e["sub"]),
                     ("結尾貼紙", e["badge"]), ("講者標籤", BRAND["speaker_label"])):
            add(k, v)
        script = getattr(sys.modules.get("__main__"), "__file__", None)
        if script and script.endswith(".py") and os.path.exists(script):
            import ast
            for node in ast.walk(ast.parse(open(script, encoding="utf-8").read())):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) and not node.value.isascii():
                    add(f"{os.path.basename(script)} 第 {node.lineno} 行", node.value)
        glyph_warning(found, "字型缺字")
        return set(found)

    def report_missing(s):
        """after sheet / render: characters that were actually drawn but missing (e.g. text built at runtime)"""
        glyph_warning({ch: [f"畫面文字「{txt[:20]}」"] for ch, txt in MISSING.items() if ch not in s.reported},
                      "畫面上實際出現的缺字")

    def L(s, scene, src):
        """local time inside `scene` of a SOURCE-second moment (sync animation beats to words)"""
        return s.tl.o(src) - s.start[scene]

    def face(s, c, t, rect=(0, 0, W, H), focus=(0.5, 0.4), zoom=1.0, punch=1.0, radius=0, card=False,
             grade=None, alpha=1.0):
        """Draw the speaker's own footage at output second t, frame-locked to the audio edit (every cut in
        KEEPS is a jump cut in the picture too).
        focus: where the face is in the source frame (0..1) — keeps it in view when a landscape shot is cropped
        to 9:16.  punch: zoom used on every other KEEPS range (e.g. 1.12) so jump cuts read as deliberate
        punch-ins instead of glitches; 1.0 = off.  rect / radius / card: picture-in-picture, e.g.
        R.face(c, t, rect=(140, 420, 800, 820), radius=30, card=True) beside an illustration."""
        assert s.src_video, "Reel(..., source_video=<recording>) is needed for face scenes"
        img = video(s.src_video, loop=False, rotate=s.rotate).frame_at(s.tl.src(t))
        z = zoom * (punch if s.tl.keep_index(t) % 2 else 1.0)
        draw_media(c, img, rect=rect, radius=radius, zoom=(z, z), pan=((0, 0), (0, 0)), grade=grade, alpha=alpha,
                   card=card, focus=focus)

    def _draw(s, c, i, t):
        n, st, fn = s.scenes[i]
        e = s.scenes[i + 1][1] if i + 1 < len(s.scenes) else s.tl.TOTAL
        fn(c, t, t - st, e - st)

    def frame(s, c, t):
        i = max(j for j, (_, st, _) in enumerate(s.scenes) if t >= st)
        n, st, _ = s.scenes[i]
        lt = t - st; kind = s.trans.get(n, "cut")
        if i > 0 and lt < s.TR and kind != "cut":
            k = eio(lt / s.TR)
            if kind == "slide":   # clip each half: drawColor/drawPaint backgrounds ignore translate
                with Xf(c, -W * k, 0):
                    c.clipRect(skia.Rect.MakeXYWH(0, 0, W, H)); s._draw(c, i - 1, t)
                with Xf(c, W * (1 - k), 0):
                    c.clipRect(skia.Rect.MakeXYWH(0, 0, W, H)); s._draw(c, i, t)
            elif kind == "zoom":
                s._draw(c, i - 1, t)
                with Xf(c, W / 2, H / 2, lerp(1.25, 1, k), 0, k):
                    c.translate(-W / 2, -H / 2); s._draw(c, i, t)
            else:
                s._draw(c, i - 1, t)
                c.save(); pth = skia.Path(); pth.addCircle(W / 2, 900, 1300 * k); c.clipPath(pth, skia.ClipOp.kIntersect, True)
                s._draw(c, i, t); c.restore()
        else:
            s._draw(c, i, t)
        if n not in s.hide_tag: top_tag(c, t, s.tag)
        if t < s.tl.END_START:
            cur = None
            for txt, t0, who in s.subs:
                if t >= t0 - 0.03: cur = (txt, t0, who)
            if cur: draw_subtitle(c, t, cur[0], cur[1], cur[2])

    def snapshot(s, t, path):
        surf = skia.Surface(W, H)
        with surf as c:
            c.clear(hx(BG)); s.frame(c, t)
        surf.makeImageSnapshot().save(path, skia.kPNG)

    def sheet(s, at=0.7, per_row=7):
        from PIL import Image
        for f in glob.glob(os.path.join(s.dir, "sheetframe_*.png")): os.remove(f)
        paths = []
        for i, (n, st, _) in enumerate(s.scenes):
            e = s.scenes[i + 1][1] if i + 1 < len(s.scenes) else s.tl.TOTAL
            t = st + (e - st) * at; p = os.path.join(s.dir, f"sheetframe_{i:02d}_{n}.png")
            s.snapshot(t, p); paths.append(p); print(f"{n:12s} start {st:6.2f}s  dur {e - st:5.2f}s  frame@{t:.2f}")
        ims = [Image.open(p).resize((300, 533)) for p in paths]
        for k in range(0, len(ims), per_row):
            row = ims[k:k + per_row]; sh = Image.new("RGB", (300 * len(row), 533), "white")
            for i, im in enumerate(row): sh.paste(im, (300 * i, 0))
            out = os.path.join(s.dir, f"sheet_{k // per_row}.png"); sh.save(out); print("sheet ->", out)
        s.report_missing()

    def render(s):
        audio, sr = sf.read(os.path.join(s.dir, "clip_audio.wav"), dtype="float32")
        surf = skia.Surface(W, H)
        cont = av.open(s.out, "w")
        vs = cont.add_stream("libx264", rate=FPS); vs.width, vs.height, vs.pix_fmt = W, H, "yuv420p"
        vs.options = {"crf": "18", "preset": "medium", "profile": "high"}
        as_ = cont.add_stream("aac", rate=sr); as_.layout = "stereo"; as_.bit_rate = 192000
        n = int(round(s.tl.TOTAL * FPS))
        for fi in range(n):
            with surf as c:
                c.clear(hx(BG)); s.frame(c, fi / FPS)
            vf = av.VideoFrame.from_ndarray(surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType), format="rgba")
            for pk in vs.encode(vf): cont.mux(pk)
            if fi % 150 == 0: print(f"frame {fi}/{n}", flush=True)
        for pk in vs.encode(): cont.mux(pk)
        pcm = np.ascontiguousarray(audio.T)
        for i in range(0, pcm.shape[1], 1024):
            af = av.AudioFrame.from_ndarray(np.ascontiguousarray(pcm[:, i:i + 1024]), format="fltp", layout="stereo")
            af.sample_rate = sr; af.pts = i
            for pk in as_.encode(af): cont.mux(pk)
        for pk in as_.encode(): cont.mux(pk)
        cont.close()
        s.verify()
        s.report_missing()

    def verify(s):
        c = av.open(s.out)
        for st in c.streams:
            print(st.type, st.codec_context.name, getattr(st.codec_context, "width", ""), getattr(st.codec_context, "height", ""),
                  round(float(st.duration * st.time_base), 2) if st.duration else None)
        print("frames", sum(1 for _ in c.decode(video=0)), "expected", int(round(s.tl.TOTAL * FPS)), "->", s.out)

    def cli(s):
        cmd = sys.argv[1] if len(sys.argv) > 1 else "sheet"
        if cmd == "audio": build_audio(s.tl, os.path.join(s.dir, "seg.wav"), os.path.join(s.dir, "clip_audio.wav"))
        elif cmd == "sheet": s.sheet()
        elif cmd == "preview":
            for x in sys.argv[2:]: s.snapshot(float(x), os.path.join(s.dir, f"preview_{float(x):05.2f}.png"))
        elif cmd == "render": s.render()
        elif cmd == "verify": s.verify()
        else: print(__doc__)
