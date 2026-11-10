"""剪法：how a clip is cut (片型, 心法, 模組, 字卡), kept apart from the channel's look (brand.json).

Layers, lowest first:
  1. the 片型's defaults (FORMATS below)
  2. a saved 剪法 ("recipe") in my-brand\\recipes.json — {"<name>": {"format": null | <FORMATS key>, "over": {key: value}}}
     ("預設" always exists). A channel's brand.json "recipe" names the one it uses unless a folder picks another.
  3. one material folder's own changes: "cut" in <folder>\\_reels_studio.json — {"recipe", "format", "over"}

The panel writes the resolved result into that same "cut" ("settings", "brief"), so the editor agent and reels_lib read
one place. Pure Python: studio_ui imports it, reels_lib loads it by path.

Only three keys change what the engine does by itself: pace (CARD_CPS), card_title (title card on / off), title_bg.
Everything else is read by the editor agent, through "brief".

recipes.json sits in my-brand\\ because the installer and the release build leave my-brand* alone.
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
RECIPES_FILE = os.path.join(HERE, "my-brand", "recipes.json")
DEFAULT = "預設"

TRI = ("on", "auto", "off")
# talk and anim are what a folder is detected as, so their pace / title card / title background stay what every channel
# had before 剪法 existed (medium, on, paper): a channel nobody touched cuts exactly as it did
_RULES_TALK = [["question", "titlecard"], ["quote", "quotecard"], ["list", "listcard"], ["number", "numbercard"],
               ["metaphor", "broll"], ["punch", "cutout"], ["turn", "zoom"], ["story", "pip"]]
FORMATS = {
    "talk": {"name": "口播 Reels", "desc": "露臉講話。跳接推近，字卡補重點，講抽象的地方切插圖。", "base": "主講人畫面",
             "def": {"pace": "medium", "zoom_every": 5, "cards": 1, "visual": 1, "motion": 1, "breath": True, "max_cards": 4,
                     "card_title": "on", "title_bg": "paper", "card_quote": "auto", "card_list": "auto", "card_number": "auto",
                     "card_chapter": "off", "mod_punch": "on", "mod_cutout": "auto", "mod_broll": "auto", "mod_pip": "auto",
                     "mod_trans": "auto", "mod_sfx": "off", "rules": _RULES_TALK}},
    "anim": {"name": "動畫解說", "desc": "只有錄音或字卡，沒有露臉。整支用插圖和字卡講。", "base": "插圖場景",
             "def": {"pace": "medium", "zoom_every": 0, "cards": 2, "visual": 2, "motion": 2, "breath": True, "max_cards": 6,
                     "card_title": "on", "title_bg": "paper", "card_quote": "on", "card_list": "on", "card_number": "on",
                     "card_chapter": "off", "mod_punch": "off", "mod_cutout": "on", "mod_broll": "on", "mod_pip": "off",
                     "mod_trans": "on", "mod_sfx": "auto",
                     "rules": [r for r in _RULES_TALK if r[1] not in ("zoom", "pip")] + [["turn", "sfx"]]}},
    "vlog": {"name": "Vlog", "desc": "生活實拍為主，字卡少、留白多，用章節卡分段。", "base": "實拍畫面",
             "def": {"pace": "slow", "zoom_every": 8, "cards": 0, "visual": 0, "motion": 0, "breath": True, "max_cards": 2,
                     "card_title": "auto", "title_bg": "photo", "card_quote": "off", "card_list": "auto", "card_number": "off",
                     "card_chapter": "on", "mod_punch": "auto", "mod_cutout": "off", "mod_broll": "off", "mod_pip": "off",
                     "mod_trans": "auto", "mod_sfx": "auto", "rules": [["question", "titlecard"], ["list", "listcard"], ["punch", "zoom"]]}},
}
TRIGGERS = {"question": "問句", "story": "講自己的經驗", "quote": "引用別人的話", "turn": "情緒轉折", "metaphor": "比喻或抽象概念",
            "list": "列舉", "punch": "金句", "number": "數字", "cta": "結尾邀請"}
ACTIONS = {"titlecard": "問句標題卡（只在開頭）", "quotecard": "引言字卡", "listcard": "清單字卡", "numbercard": "數字字卡",
           "broll": "滿版插圖 B-roll", "cutout": "去背大字", "zoom": "推近", "pip": "子母畫面", "sfx": "音效"}
# value checks: (kind, options)
KEYS = {"pace": ("one", ("fast", "medium", "slow")), "zoom_every": ("int", (0, 10)), "cards": ("int", (0, 2)),
        "visual": ("int", (0, 2)), "motion": ("int", (0, 2)), "breath": ("bool", None), "max_cards": ("int", (1, 8)),
        "card_title": ("one", TRI), "title_bg": ("one", ("paper", "photo")), "card_quote": ("one", TRI),
        "card_list": ("one", TRI), "card_number": ("one", TRI), "card_chapter": ("one", TRI), "mod_punch": ("one", TRI),
        "mod_cutout": ("one", TRI), "mod_broll": ("one", TRI), "mod_pip": ("one", TRI), "mod_trans": ("one", TRI),
        "mod_sfx": ("one", TRI), "rules": ("rules", None)}


def clean_over(over):
    """keep only known keys with valid values"""
    out = {}
    for k, v in (over or {}).items():
        if k not in KEYS: continue
        kind, opt = KEYS[k]
        if kind == "one" and v in opt: out[k] = v
        elif kind == "int" and isinstance(v, (int, float)) and not isinstance(v, bool): out[k] = max(opt[0], min(opt[1], int(v)))
        elif kind == "bool" and isinstance(v, bool): out[k] = v
        elif kind == "rules" and isinstance(v, list):
            out[k] = [[a, b] for a, b in (r for r in v if isinstance(r, (list, tuple)) and len(r) == 2)
                      if a in TRIGGERS and b in ACTIONS][:30]
    return out


def clean_format(f):
    return f if f in FORMATS else None


def load_recipes(path=None):
    try: raw = json.load(open(path or RECIPES_FILE, encoding="utf-8"))
    except Exception: raw = {}
    out = {}
    for name, r in (raw or {}).items():
        if isinstance(r, dict) and isinstance(name, str) and name.strip():
            out[name] = {"format": clean_format(r.get("format")), "over": clean_over(r.get("over"))}
    out.setdefault(DEFAULT, {"format": None, "over": {}})
    return out


def legacy_over(layout):
    """what an older brand.json "layout" said about the keys that moved to 剪法 (pace, title card, its background)"""
    layout = layout or {}
    over = {}
    if layout.get("pace") in KEYS["pace"][1]: over["pace"] = layout["pace"]
    if "title_card" in layout: over["card_title"] = "on" if layout["title_card"] else "off"
    if layout.get("title_bg") in KEYS["title_bg"][1]: over["title_bg"] = layout["title_bg"]
    return over


def resolve(fmt, recipe_over=None, folder_over=None):
    """the full settings for a 片型 + the 剪法's changes + a folder's own changes"""
    s = json.loads(json.dumps(FORMATS[fmt if fmt in FORMATS else "talk"]["def"]))
    s.update(clean_over(recipe_over)); s.update(clean_over(folder_over))
    return s


_PACE = {"fast": "快（每 2–3 秒畫面要有變化）", "medium": "中（每 3–4 秒）", "slow": "慢（每 4–6 秒，留白多）"}
_TRI = {"on": "一定用", "auto": "剪輯師判斷", "off": "不用"}
_LEVEL = {"cards": ["少，只放最重要的", "適中", "多，重點都做成字卡"], "visual": ["人和字幕為主", "平衡", "插圖為主"],
          "motion": ["沉穩", "適中", "活潑"]}
NAMES = {"card_title": "問句標題卡", "card_quote": "引言字卡", "card_list": "清單字卡", "card_number": "數字字卡",
         "card_chapter": "章節卡", "mod_punch": "跳接推近", "mod_cutout": "去背大字", "mod_broll": "滿版插圖 B-roll",
         "mod_pip": "子母畫面", "mod_trans": "轉場", "mod_sfx": "音效"}


def brief(fmt, s, recipe_name=None, folder_keys=()):
    """the settings in plain words, one line each, for the editor agent (written into _reels_studio.json "cut")"""
    f = FORMATS[fmt if fmt in FORMATS else "talk"]
    mark = lambda k: "（這個資料夾另外改的）" if k in folder_keys else ""
    lines = [f"片型：{f['name']}，{f['desc']}" + mark("format")]
    if recipe_name: lines.append(f"剪法：{recipe_name}")
    lines += [
        f"節奏：{_PACE[s['pace']]}" + mark("pace"),
        ("推近：主講人畫面每 %d 秒推近一次（跳接放大）" % s["zoom_every"] if s["zoom_every"] else "推近：不做週期性的推近") + mark("zoom_every"),
        f"字卡多寡：{_LEVEL['cards'][s['cards']]}；一支最多 {s['max_cards']} 張字卡" + mark("cards") + mark("max_cards"),
        f"畫面以什麼為主：{_LEVEL['visual'][s['visual']]}" + mark("visual"),
        f"動態強度：{_LEVEL['motion'][s['motion']]}" + mark("motion"),
        "金句講完停 0.5 秒再接下一句" if s["breath"] else "金句後不特別留白",
        "標題卡背景：" + ("免費圖庫照片" if s["title_bg"] == "photo" else "跟影片一樣的背景") + mark("title_bg"),
    ]
    lines.append("字卡：" + "、".join(f"{NAMES[k]} {_TRI[s[k]]}{mark(k)}" for k in
                                     ("card_title", "card_quote", "card_list", "card_number", "card_chapter")))
    lines.append("手法：" + "、".join(f"{NAMES[k]} {_TRI[s[k]]}{mark(k)}" for k in
                                    ("mod_punch", "mod_broll", "mod_cutout", "mod_pip", "mod_trans", "mod_sfx")))
    if s["rules"]:
        lines.append("規則（讀逐字稿時照這些判斷；對應的字卡或手法是「不用」時就跳過）："
                     + "；".join(f"講到{TRIGGERS[a]}就用{ACTIONS[b]}" for a, b in s["rules"]) + mark("rules"))
    lines.append("「一定用」= 每次符合規則都做；「剪輯師判斷」= 照上面的多寡和節奏決定要不要做、做幾次；「不用」= 不做。")
    return lines


def recipe_name_for(project, brand):
    """the 剪法 a folder uses: its own pick, else its channel's, else 預設"""
    cut = (project or {}).get("cut") or {}
    return cut.get("recipe") or (brand or {}).get("recipe") or DEFAULT


def engine_settings(project, brand, recipes=None):
    """pace / card_title / title_bg for reels_lib: the folder's resolved cut when the panel wrote one, else the
    channel's 剪法, else what an older brand.json layout said"""
    cut = (project or {}).get("cut") or {}
    if isinstance(cut.get("settings"), dict):
        return resolve(cut.get("format_used"), cut["settings"])
    recipes = recipes if recipes is not None else load_recipes()
    name = recipe_name_for(project, brand)
    r = recipes.get(name) or recipes[DEFAULT]
    over = dict(r["over"])
    if not (brand or {}).get("recipe"):          # a channel not migrated yet: its old layout still counts
        over = {**legacy_over((brand or {}).get("layout")), **over}
    return resolve(cut.get("format") or r["format"], over, cut.get("over"))
