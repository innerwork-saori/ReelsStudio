"""Font picker for brand.json: list installed fonts that can set Traditional Chinese, show samples, check text.

usage:
  python fonts.py list [out.png] [--all]
                                        numbered list of installed fonts covering Traditional Chinese (Taiwan forms
                                        first, then HK; --all adds Japanese / Simplified-form fonts) + a sample
                                        sheet (default <brand dir>/fonts_sheet.png). Read the sheet before choosing.
  python fonts.py check "<font>" "<text>" [--weight 700]
                                        characters of <text> that <font> cannot draw (they would render as boxes)
  python fonts.py free                  recommended free fonts (open licences, fine for commercial videos) + links

<font> is a family name as `list` prints it (e.g. "Noto Sans TC") or a font file name / path.
In brand.json:  "font": "<family name or file>",  "font_weight": 400 | 500 | 700 ...
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import skia

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 300 frequent characters, many with distinct Traditional forms — a font must have (almost) all of them
TC_SAMPLE = ("的一是不了人我在有他這中大來上國個到說們為子和你地出道也時年得就那要下以生會自著去之過家學對可她裡後"
             "小麼心多天而能好都然沒日於起還發成事只作當想看文無開手十用主行方又如前所本見經頭面公同三已老從動兩長"
             "知民樣現分將外但身些與高意進把法此實回二理美點月明其種聲全工己話兒者向情部正名定女問力機給等幾很業最"
             "間新什打便位因重被走電四第門相次東政海口使教西再平真聽世氣信北少關並內加化由卻代軍產入先山五太水萬市"
             "眼體別處總才場師書比住員九笑性通目華報立馬命張活難神數件安表原車白應路期叫死常提感金何更反合放做系計"
             "或司利受光王果親界及今京務制解各任至清物台象記邊共風戰干接它許八特覺望直服毛林題建南度統色字請交愛讓"
             "灣臺龜廳鬱齣嘗嚮")
SHEET_TEXT = ["你有沒有想過「休息」", "也是一種能力？明明裂開了"]   # left: weight 400, right: boldest <= 700

FREE_FONTS = [
    ("jf open 粉圓", "圓潤可愛、字幕很好讀（Reels Studio 預設，已隨安裝包安裝）", "SIL OFL 1.1",
     "https://github.com/justfont/open-huninn-font"),
    ("思源黑體 Noto Sans TC", "乾淨的黑體，粗細齊全，最萬用（Windows 11 多半已內建）", "SIL OFL 1.1",
     "https://fonts.google.com/noto/specimen/Noto+Sans+TC"),
    ("台北黑體 Taipei Sans TC", "現代感黑體，標題很有力", "SIL OFL 1.1",
     "https://sites.google.com/view/jtfoundry"),
    ("源泉圓體", "圓體，比粉圓成熟一點", "SIL OFL 1.1", "https://github.com/ButTaiwan/gensen-font"),
    ("霞鶩文楷 TC", "手寫楷書感，適合文青、故事、療癒內容", "SIL OFL 1.1", "https://github.com/lxgw/LXGWWenKaiTC"),
    ("芫荽 iansui", "清秀的手寫風，親切", "SIL OFL 1.1", "https://github.com/ButTaiwan/iansui"),
]


def load(font, weight=400):
    """typeface for a family name or a font file (name in the Windows font folders, or a path); None if missing"""
    from reels_lib import load_typeface
    return load_typeface(font, weight)[0]


def missing(tf, text):
    """characters of text the typeface has no glyph for (whitespace and subtitle markup ignored)"""
    chars = sorted({ch for ch in text if not ch.isspace() and ch not in "【】|"})
    return [ch for ch, g in zip(chars, tf.unicharsToGlyphs([ord(ch) for ch in chars])) if g == 0]


def weights(family):
    ss = skia.FontMgr.RefDefault().matchFamily(family)
    return sorted({ss.getStyle(i)[0].weight() for i in range(ss.count())
                   if ss.getStyle(i)[0].slant() == skia.FontStyle.kUpright_Slant}) if ss else []


# fonts that contain these characters but draw many of them in Japanese / Simplified / Korean standard forms
OTHER_FORMS = (" SC", " JP", " K", "YaHei", "SimSun", "SimHei", "DengXian", "KaiTi", "FangSong", "Meiryo", "Yu ",
               "MS ", "Malgun", "Arial Unicode")
HK_FORMS = (" HK", "HKSCS")

_REAL = {}
def real_name(name):
    """the font's own family name — Windows lists many fonts by a localised name (小瀨字體 is Kosefont JP)"""
    if name not in _REAL:
        tf = load(name)
        _REAL[name] = tf.getFamilyName() if tf else name
    return _REAL[name]

def region(name):
    names = (name, real_name(name))
    if any(k in n for n in names for k in HK_FORMS): return "香港字形"
    if any(k in n for n in names for k in OTHER_FORMS) or any(n in ("Source Han Sans", "Source Han Serif") for n in names): return "其他"
    return "台灣字形"

def tc_families(include_other=False):
    fm, out = skia.FontMgr.RefDefault(), []
    for i in range(fm.countFamilies()):
        name = fm.getFamilyName(i)
        if name.startswith("@") or "ExtB" in name: continue   # vertical-writing aliases / rare-character supplements
        if not include_other and region(name) == "其他": continue
        tf = load(name)
        if tf is None: continue
        if len(missing(tf, TC_SAMPLE)) <= 2: out.append((name, weights(name)))
    return sorted(out, key=lambda x: (region(x[0]) != "台灣字形", x[0].lower()))


def sheet(fams, out):
    row, w = 150, 1400
    surf = skia.Surface(w, row * len(fams) + 20)
    with surf as c:
        c.clear(skia.ColorWHITE)
        label = skia.Font(skia.Typeface.MakeFromName("Microsoft JhengHei", skia.FontStyle.Bold()) or skia.Typeface.MakeDefault(), 24)
        for i, (name, ws) in enumerate(fams):
            y = 20 + i * row
            c.drawString(f"{i + 1}. {name}（{region(name)}）" + ("　← 預設" if "粉圓" in name or "huninn" in name.lower() else ""),
                         20, y + 30, label, skia.Paint(Color=skia.ColorSetRGB(0x8C, 0x5F, 0x5A)))
            heavy = max([x for x in ws if x <= 700] or [400])
            for j, (wt, txt) in enumerate(((400, SHEET_TEXT[0]), (heavy, SHEET_TEXT[1]))):
                tf = load(name, wt) or load(name)
                c.drawString(txt, 20 + j * 700, y + 100, skia.Font(tf, 48), skia.Paint(AntiAlias=True, Color=skia.ColorSetRGB(0x3D, 0x2C, 0x29)))
            c.drawLine(20, y + row - 10, w - 20, y + row - 10, skia.Paint(Color=skia.ColorSetRGB(0xE3, 0xDB, 0xD3)))
    surf.makeImageSnapshot().save(out, skia.kPNG)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd == "list":
        from reels_lib import BRAND_DIR
        rest = [a for a in sys.argv[2:] if a != "--all"]
        out = rest[0] if rest else os.path.join(BRAND_DIR, "fonts_sheet.png")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        fams = tc_families(include_other="--all" in sys.argv)
        for i, (name, ws) in enumerate(fams):
            print(f"{i + 1:2d}. {name}（{region(name)}）    粗細: {', '.join(map(str, ws)) or '—'}")
        sheet(fams, out)
        print(f"\n{len(fams)} fonts can set Traditional Chinese. samples (left 400, right boldest ≤700) -> {out}")
        if "--all" not in sys.argv: print("Japanese / Simplified / Korean-form fonts are hidden; add --all to include them.")
    elif cmd == "check":
        args = sys.argv[2:]; wt = 400
        if "--weight" in args:
            k = args.index("--weight"); wt = int(args[k + 1]); del args[k:k + 2]
        tf = load(args[0], wt)
        if tf is None: sys.exit(f"font not found: {args[0]}")
        miss = missing(tf, args[1])
        print(f"{tf.getFamilyName()} weight {tf.fontStyle().weight()}: " + ("all characters OK" if not miss else "MISSING " + " ".join(miss)))
    elif cmd == "free":
        for name, look, lic, url in FREE_FONTS:
            print(f"- {name}｜{look}｜{lic}｜{url}")
        print("\n下載後在字型檔（.ttf / .otf）上按右鍵 → 安裝，再重新執行 python fonts.py list。")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
