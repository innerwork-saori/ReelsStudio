"""Reels Studio 控制台：本機網頁面板（做影片、風格），給不想打字的使用者用。只聽 127.0.0.1，不需要網路。

usage: python studio_ui.py [--port 8765] [--no-browser]
The desktop shortcut runs it with pythonw (no console window), so output goes to studio_ui.log next to this file.
Already running? It just opens the browser on the running one. It exits by itself 15 minutes after the page is closed.

Edits the same files the agents read: <brand dir>\brand.json and BRAND.md. BRAND.md is also edited by Claude, so the
panel only rewrites the "- 欄位：值" lines the user changed and leaves every other line alone.
"""
import ast, glob, json, os, re, secrets, shutil, subprocess, sys, tempfile, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.join(HERE, "ui")
STATE_FILE = os.path.join(HERE, "ui_state.json")       # recent project folders, last brand
TMP = tempfile.mkdtemp(prefix="reels_studio_ui_")
TOKEN = secrets.token_urlsafe(18)
APP_ID = "reels-studio-ui"
def app_version():
    """the release number the installer wrote; read on every request, so the footer is right even if the panel
    started before the installer finished"""
    try: return open(os.path.join(HERE, "VERSION"), encoding="utf-8").read().strip()
    except OSError: return ""

# the page is read once at start so a running server never pairs a newer page with its older code;
# VERSION changes whenever the code, the page or the release number changes, so a reinstall makes the next
# launch replace the old server
INDEX_HTML = open(os.path.join(UI_DIR, "index.html"), encoding="utf-8").read()
VERSION = __import__("hashlib").sha1(open(os.path.abspath(__file__), "rb").read() + INDEX_HTML.encode("utf-8")
                                     + app_version().encode("utf-8")).hexdigest()[:12]
IDLE_EXIT = 15 * 60
RELEASES = "https://github.com/innerwork-saori/ReelsStudio/releases"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
MEDIA_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".mp4": "video/mp4",
             ".mov": "video/quicktime", ".webm": "video/webm", ".m4a": "audio/mp4", ".mp3": "audio/mpeg"}
SOURCE_EXT = (".mp3", ".m4a", ".wav", ".mp4", ".mov")
last_ping = time.time()

if sys.stdout is None or sys.stderr is None:            # pythonw: no console
    log = open(os.path.join(HERE, "studio_ui.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = log
else:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------- palettes and defaults straight from reels_lib.py (no skia import needed) ----------------
def _lib_constants():
    tree = ast.parse(open(os.path.join(HERE, "reels_lib.py"), encoding="utf-8").read())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and \
                node.targets[0].id in ("PALETTES", "BRAND_DEFAULTS", "STYLE_OPTIONS", "STYLE_PRESETS", "LAYOUT_OPTIONS"):
            out[node.targets[0].id] = eval(compile(ast.Expression(node.value), "reels_lib", "eval"), {"dict": dict})
    return out["PALETTES"], out["BRAND_DEFAULTS"], out["STYLE_OPTIONS"], out["STYLE_PRESETS"], out["LAYOUT_OPTIONS"]

PALETTES, BRAND_DEFAULTS, STYLE_OPTIONS, STYLE_PRESETS, LAYOUT_OPTIONS = _lib_constants()

def resolved_style(s):
    """the look a brand.json "style" produces (same rule as reels_lib._style)"""
    s = s or {}
    out = dict(STYLE_PRESETS.get(s.get("preset"), STYLE_PRESETS["handmade"]))
    for k, opts in STYLE_OPTIONS.items():
        if s.get(k) in opts: out[k] = s[k]
    return out

def resolved_layout(l):
    """the layout rules a brand.json "layout" produces (same rule as reels_lib._layout)"""
    out = dict(BRAND_DEFAULTS["layout"])
    for k, v in (l or {}).items():
        if k in LAYOUT_OPTIONS: out[k] = v if v in LAYOUT_OPTIONS[k] else out[k]
        elif k in out: out[k] = bool(v)
    return out


# ---------------- small helpers ----------------
def read_json(p, default=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return default

def write_text(p, s):
    """write UTF-8, keeping the file's existing line endings (Claude may have written it with CRLF)"""
    os.makedirs(os.path.dirname(p), exist_ok=True)
    nl = "\r\n" if os.path.exists(p) and b"\r\n" in open(p, "rb").read() else "\n"
    with open(p, "w", encoding="utf-8", newline=nl) as f: f.write(s)

def state():
    return read_json(STATE_FILE, {}) or {}

def save_state(**kw):
    s = state(); s.update(kw)
    write_text(STATE_FILE, json.dumps(s, ensure_ascii=False, indent=2))

def run_py(args, env=None, timeout=300):
    """run a toolkit script with this Python; returns (exit code, combined output)"""
    e = dict(os.environ, PYTHONIOENCODING="utf-8", **(env or {}))
    p = subprocess.run([sys.executable] + args, cwd=HERE, env=e, capture_output=True, timeout=timeout,
                       creationflags=NO_WINDOW)
    return p.returncode, (p.stdout + p.stderr).decode("utf-8", "replace")

def under(path, roots):
    path = os.path.normcase(os.path.abspath(path))
    return any(path == os.path.normcase(os.path.abspath(r)) or path.startswith(os.path.normcase(os.path.abspath(r)) + os.sep)
               for r in roots)

def clean_path(p):
    return (p or "").strip().strip('"').strip()

# Windows errors that mean "the disk is gone or failing", not "this file is wrong"
DISK_ERRORS = {21: "磁碟還沒準備好", 1117: "磁碟讀取錯誤", 1167: "裝置沒有連接", 1006: "磁碟已經被拔除", 55: "網路磁碟已經斷線",
               59: "網路磁碟發生錯誤", 64: "網路磁碟已經斷線", 433: "裝置不存在", 483: "硬體錯誤", 1005: "磁碟無法辨識"}

def win_error_of(path):
    """the Windows error code for opening path; Python's open() reports only a C errno (1117 shows up as EINVAL)"""
    if os.name != "nt" or not path: return None
    import ctypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = ctypes.c_void_p
    h = k32.CreateFileW(str(path), 0x80000000, 7, None, 3, 0x02000000, None)   # GENERIC_READ, share all, OPEN_EXISTING, BACKUP_SEMANTICS (dirs too)
    if h in (None, ctypes.c_void_p(-1).value): return ctypes.get_last_error()
    k32.CloseHandle(ctypes.c_void_p(h)); return None

def friendly_os_error(e, path=""):
    """a sentence a non-technical user can act on"""
    path = path or getattr(e, "filename", "") or ""
    drive = os.path.splitdrive(os.path.abspath(path))[0] if path else ""
    where = f" {drive} 磁碟" if drive else "這個磁碟"
    code = getattr(e, "winerror", None) or win_error_of(path)
    if code in DISK_ERRORS:
        return (f"讀不到{where}上的檔案（{DISK_ERRORS[code]}）。如果是外接硬碟或隨身碟，通常是連線斷了："
                "請把 USB 線拔掉重新插上（或換一個 USB 孔），等電腦重新認到之後再試一次。")
    if isinstance(e, PermissionError):
        return f"沒有權限讀取這個位置，或檔案正在被其他程式使用中。{os.path.basename(getattr(e, 'filename', '') or '')}"
    if isinstance(e, FileNotFoundError):
        return "找不到這個資料夾或檔案，可能已經被移動或刪除。"
    return f"讀取檔案時發生錯誤：{e.strerror or e}"

def try_read(fn, *args, default=None, problems=None):
    """run a file operation; on OSError remember a friendly message and return default"""
    try:
        return fn(*args)
    except OSError as e:
        if problems is not None:
            msg = friendly_os_error(e, args[0] if args and isinstance(args[0], str) else "")
            if msg not in problems: problems.append(msg)
        return default

def read_text(p, enc="utf-8"):
    with open(p, encoding=enc) as f: return f.read()


# ---------------- brands ----------------
def brand_dirs():
    """every channel folder: my-brand, my-brand-*, and REELS_BRAND if set"""
    dirs = [os.path.join(HERE, "my-brand")]
    dirs += sorted(d for d in glob.glob(os.path.join(HERE, "my-brand-*")) if os.path.isdir(d))
    env = os.environ.get("REELS_BRAND")
    if env and os.path.normcase(os.path.abspath(env)) not in [os.path.normcase(d) for d in dirs]: dirs.append(env)
    return dirs

def check_brand_dir(d):
    if not any(os.path.normcase(os.path.abspath(d)) == os.path.normcase(x) for x in brand_dirs()):
        raise ValueError("不認得這個風格資料夾")
    return d


# BRAND.md lines the panel can edit: (section, label, other labels Claude may have used)
MD_FIELDS = [
    ("頻道", "內容類型", []),
    ("頻道", "主要講者", ["主持人", "講者"]),
    ("頻道", "常一起出現的人與字幕標示", ["字幕標示"]),
    ("頻道", "目標觀眾", []),
    ("頻道", "發布平台", []),
    ("頻道", "發文頻率", []),
    ("文案", "語氣", []),
    ("文案", "結尾行動（CTA）", ["CTA"]),
    ("文案", "固定 hashtag", []),
    ("文案", "Hashtag 數量", []),
    ("文案", "禁用的詞或 hashtag", ["禁用的 hashtag", "禁用的詞"]),
    ("文案", "Emoji", []),
    ("影片", "露臉", []),
    ("影片", "自由創作方向", []),
    ("影片", "參考帳號或影片", []),
]
AUTO_FIELDS = [("頻道", "名稱"), ("影片", "版面風格"), ("影片", "版面規則"), ("影片", "配色"), ("影片", "字型"),
               ("影片", "結尾卡")]   # filled from brand.json

def md_line_re(label):
    return re.compile(r"^- " + re.escape(label) + r"：(.*)$", re.M)

def template_md():
    return open(os.path.join(HERE, "brand_template", "BRAND.md"), encoding="utf-8").read()

def is_placeholder(v):
    v = v.strip()
    return not v or v == "未設定" or (v.startswith("（") and v.endswith("）"))

def md_get(md, label, aliases=()):
    """(label actually used in the file, value) — value '' when missing or still the template placeholder"""
    for lab in (label, *aliases):
        m = md_line_re(lab).search(md)
        if m: return lab, ("" if is_placeholder(m.group(1)) else m.group(1).strip())
    return None, ""

def md_set(md, section, label, value):
    """replace the value of one '- label：' line, or add the line at the end of its section"""
    rx = md_line_re(label)
    if rx.search(md):
        return rx.sub(lambda m: f"- {label}：{value}", md, count=1)
    sec = re.search(r"^## " + re.escape(section) + r"\s*$", md, re.M)
    if not sec:
        other = re.search(r"^## 其他偏好", md, re.M)
        block = f"## {section}\n- {label}：{value}\n\n"
        return md[:other.start()] + block + md[other.start():] if other else md.rstrip("\n") + "\n\n" + block
    nxt = re.search(r"^## ", md[sec.end():], re.M)
    end = sec.end() + (nxt.start() if nxt else len(md) - sec.end())
    body = md[sec.end():end].rstrip("\n")
    return md[:sec.end()] + body + f"\n- {label}：{value}\n\n" + md[end:].lstrip("\n")

STYLE_NAMES = {"handmade": "手作便條", "clean": "俐落簡約", "magazine": "雜誌感", "notebook": "筆記本", "street": "街頭活力",
               "free": "自由創作"}
LAYOUT_NAMES = {"subtitle_pos": {"low": "下方", "middle": "畫面中間"}, "subtitle_size": {"s": "小", "m": "中", "l": "大"},
                "pace": {"fast": "快（每 2–3 秒換畫面）", "medium": "中（每 3–4 秒）", "slow": "慢（每 4–6 秒，留白多）"}}
STYLE_PART_NAMES = {"subtitle": "字幕", "title": "標題卡", "background": "背景", "line": "線條", "motion": "動畫", "end": "結尾卡"}
STYLE_OPTION_NAMES = {
    "subtitle": {"box": "白框", "outline": "描邊字", "pill": "膠囊條", "dark": "深色框"},
    "title": {"note": "便條紙", "bold": "大字", "line": "細框卡", "magazine": "色塊斜帶"},
    "background": {"blobs": "手繪色塊", "plain": "純色", "grid": "方格紙", "gradient": "柔和漸層"},
    "line": {"bold": "粗墨線", "thin": "細線", "soft": "淡細線"},
    "motion": {"bouncy": "活潑彈跳", "snappy": "俐落", "gentle": "柔和"},
    "end": {"classic": "經典", "minimal": "極簡", "card": "名片卡"}}

NOTES_SECTION = "其他補充（控制台填寫）"   # the panel's 「其他」 box owns this section; Claude's 其他偏好 is left alone

def md_section(md, title):
    """body of '## title' (until the next '## '), or None"""
    m = re.search(r"^## " + re.escape(title) + r"[ \t]*\n", md, re.M)
    if not m: return None
    nxt = re.search(r"^## ", md[m.end():], re.M)
    return md[m.end(): m.end() + nxt.start() if nxt else len(md)].strip()

def md_set_section(md, title, body):
    """replace the body of '## title', add the section at the end, or drop it when body is empty"""
    m = re.search(r"^## " + re.escape(title) + r"[ \t]*\n", md, re.M)
    block = f"## {title}\n{body.strip()}\n\n" if body.strip() else ""
    if m:
        nxt = re.search(r"^## ", md[m.end():], re.M)
        end = m.end() + nxt.start() if nxt else len(md)
        out = md[:m.start()] + block + md[end:]
        if not block and not md[end:].strip(): out = out.rstrip("\n") + "\n"   # removed the last section: no stray blank line
        return out
    return md.rstrip("\n") + "\n\n" + block if block else md

def brand_summary(b):
    pal = b.get("palette", "cream")
    over = "、".join(f"{k} {v}" for k, v in (b.get("colors") or {}).items())
    font = b.get("font", "")
    e = b.get("end_card", {})
    icon = {"mic": "麥克風", "play": "播放", "heart": "愛心", "star": "星星", "logo": "自己的 logo ", "none": "無"}.get(e.get("icon"), e.get("icon"))
    st = resolved_style(b.get("style"))
    preset = (b.get("style") or {}).get("preset", "handmade")
    lay = resolved_layout(b.get("layout"))
    onoff = lambda v: "有" if v else "不要"
    if preset == "free":
        look = ("`free`（自由創作）：剪輯師依下面的「自由創作方向」和「參考帳號或影片」每支自己設計標題、字幕、背景、"
                "裝飾和轉場（STYLE.md 第 12 節）；引擎內建的樣子只當備用")
    else:
        look = f"`{preset}`（{STYLE_NAMES.get(preset, preset)}）：" + "、".join(
            f"{STYLE_PART_NAMES[k]} {STYLE_OPTION_NAMES[k].get(v, v)}" for k, v in st.items()) + "。剪片引擎會自動套用，不要另外改畫成其他風格"
    return {
        "版面風格": look,
        "版面規則": f"開頭標題卡 {onoff(lay['title_card'])}、結尾卡 {onoff(lay['end_card'])}、上方標籤 {onoff(lay['top_tag'])}、"
                    f"字幕在{LAYOUT_NAMES['subtitle_pos'][lay['subtitle_pos']]}・{LAYOUT_NAMES['subtitle_size'][lay['subtitle_size']]}、"
                    f"節奏 {LAYOUT_NAMES['pace'][lay['pace']]}",
        "配色": f"`{pal}`" + (f"，改色：{over}" if over else ""),
        "字型": f"{font}" + (f"，粗細 {b['font_weight']}" if b.get("font_weight") else ""),
        "結尾卡": f"{icon}圖示、貼紙「{e.get('badge') or '無'}」、按鈕「{e.get('cta', '')}」、小字「{e.get('sub', '')}」",
    }


def load_brand(d):
    p = os.path.join(d, "brand.json")
    exists = os.path.exists(p)
    b = json.loads(json.dumps(BRAND_DEFAULTS))
    raw = read_json(p, {}) if exists else {}
    for k, v in raw.items():
        if isinstance(v, dict) and isinstance(b.get(k), dict): b[k].update(v)
        else: b[k] = v
    if "font_weight" not in raw: b.pop("font_weight", None)   # "自動" in the form; saving must not add it
    if not exists: b["style"] = {"preset": "free"}            # a channel not set up yet starts as 自由創作
    md_p = os.path.join(d, "BRAND.md")
    md = open(md_p, encoding="utf-8").read() if os.path.exists(md_p) else ""
    fields = {}
    for sec, lab, al in MD_FIELDS:
        fields[lab] = md_get(md, lab, al)[1]
    fields["其他補充"] = md_section(md, NOTES_SECTION) or ""
    known = {lab for _, lab, al in MD_FIELDS for lab in (lab, *al)} | {lab for _, lab in AUTO_FIELDS}
    extra = [m.group(1) for m in re.finditer(r"^- ([^：\n]{1,20})：", md, re.M) if m.group(1) not in known]
    return {"dir": d, "folder": os.path.basename(d), "exists": exists, "brand": b, "fields": fields,
            "md_exists": bool(md), "md_extra": len(extra) + len(re.findall(r"^```", md, re.M)) // 2,
            "preview": file_url(os.path.join(d, "brand_preview.png")) if os.path.exists(os.path.join(d, "brand_preview.png")) else None,
            "logo": logo_url(d)}


def merge_brand(d, form):
    """brand.json content for the form values, keeping keys the panel does not show"""
    old = read_json(os.path.join(d, "brand.json"), {}) or {}
    b = json.loads(json.dumps(old))
    f = form["brand"]
    b["name"] = f.get("name", "").strip() or "我的頻道"
    b["tag"] = f.get("tag", "").strip() or None
    b["palette"] = f.get("palette") if f.get("palette") in PALETTES else "cream"
    colors = dict(old.get("colors") or {})
    for role in ("accent", "highlight"):
        v = (f.get("colors") or {}).get(role)
        if v and re.fullmatch(r"#[0-9A-Fa-f]{6}", v): colors[role] = v.upper()
        else: colors.pop(role, None)
    b["colors"] = colors
    b["font"] = f.get("font") or BRAND_DEFAULTS["font"]
    if f.get("font_weight"): b["font_weight"] = int(f["font_weight"])
    else: b.pop("font_weight", None)
    if "speaker_label" in f:                       # not on the page any more (BRAND.md says who gets which label)
        b["speaker_label"] = f["speaker_label"].strip() or "主持人"
    e = dict(old.get("end_card") or BRAND_DEFAULTS["end_card"])
    for k in ("icon", "badge", "cta", "sub", "guest_prefix", "logo_shape"):
        if k in (f.get("end_card") or {}): e[k] = f["end_card"][k].strip()
    if e.get("icon") not in ("mic", "play", "heart", "star", "logo", "none"): e["icon"] = "play"
    if e.get("logo_shape") not in ("original", "circle", "rounded"): e.pop("logo_shape", None)
    b["end_card"] = e
    if isinstance(f.get("style"), dict):         # store the preset + only the elements changed from it
        st = f["style"]
        preset = st.get("preset") if st.get("preset") in STYLE_PRESETS else "handmade"
        style = {"preset": preset}
        for k, opts in STYLE_OPTIONS.items():
            if st.get(k) in opts and st[k] != STYLE_PRESETS[preset][k]: style[k] = st[k]
        if style == {"preset": "handmade"} and not old.get("style"): b.pop("style", None)   # untouched original look
        else: b["style"] = style
    if isinstance(f.get("layout"), dict):        # store only the rules changed from the defaults
        lay = {k: v for k, v in resolved_layout(f["layout"]).items() if v != BRAND_DEFAULTS["layout"][k]}
        if lay: b["layout"] = lay
        else: b.pop("layout", None)
    return old, b


def save_brand(form):
    d = check_brand_dir(form["dir"])
    old, b = merge_brand(d, form)
    os.makedirs(d, exist_ok=True)
    for fn in ("brand.json", "BRAND.md"):                    # one backup of the previous version
        if os.path.exists(os.path.join(d, fn)): shutil.copy2(os.path.join(d, fn), os.path.join(d, fn + ".bak"))
    write_text(os.path.join(d, "brand.json"), json.dumps(b, ensure_ascii=False, indent=2) + "\n")

    md_p = os.path.join(d, "BRAND.md")
    new_md = not os.path.exists(md_p)
    md = template_md() if new_md else open(md_p, encoding="utf-8").read()
    if new_md:
        md = md.replace("> 由 Reels Studio 第一次使用時的問答產生。", "> 由 Reels Studio 控制台建立。")
    if new_md or old.get("name") != b["name"]:
        md = re.sub(r"^# 頻道設定：.*$", f"# 頻道設定：{b['name']}", md, count=1, flags=re.M)
        if not md_get(md, "名稱")[1] or new_md: md = md_set(md, "頻道", "名稱", b["name"])
    summ = brand_summary(b)
    changed = {"配色": (old.get("palette"), old.get("colors")) != (b["palette"], b["colors"]),
               "字型": (old.get("font"), old.get("font_weight")) != (b["font"], b.get("font_weight")),
               "結尾卡": old.get("end_card") != b["end_card"],
               "版面風格": (old.get("style") or {}) != (b.get("style") or {}),
               "版面規則": resolved_layout(old.get("layout")) != resolved_layout(b.get("layout"))}
    for lab, ch in changed.items():
        if new_md or ch: md = md_set(md, "影片", lab, summ[lab])
    for sec, lab, al in MD_FIELDS:                           # only lines the user actually changed
        new = (form.get("fields") or {}).get(lab)
        if new is None: continue
        new = " ".join(new.split())
        used, cur = md_get(md, lab, al)
        if new == cur or (not new and not cur): continue
        md = md_set(md, sec, used or lab, new or "未設定")
    notes = (form.get("fields") or {}).get("其他補充")
    if notes is not None:
        notes = "\n".join(l.rstrip() for l in notes.strip().splitlines())
        if notes != (md_section(md, NOTES_SECTION) or ""): md = md_set_section(md, NOTES_SECTION, notes)
    write_text(md_p, md)
    return b


def preview(form, real=False):
    """render brand_preview.png for the form values; real=False renders from a temp copy so nothing is saved"""
    d = check_brand_dir(form["dir"])
    if real:
        src, out = d, os.path.join(d, "brand_preview.png")
    else:
        src = os.path.join(TMP, "brand_" + secrets.token_hex(4)); os.makedirs(src)
        _, b = merge_brand(d, form)
        write_text(os.path.join(src, "brand.json"), json.dumps(b, ensure_ascii=False, indent=2))
        if os.path.exists(os.path.join(d, "logo.png")): shutil.copy2(os.path.join(d, "logo.png"), os.path.join(src, "logo.png"))
        out = os.path.join(src, "brand_preview.png")
    code, text = run_py(["brand_preview.py", out], env={"REELS_BRAND": src})
    if code != 0 or not os.path.exists(out):
        return {"ok": False, "error": text[-1500:]}
    return {"ok": True, "image": file_url(out) + f"&v={int(time.time())}", "warnings": preview_warnings(text)}


def preview_warnings(text):
    """brand_preview / reels_lib output -> [{kind: font | glyph | other, text}] — each kind gets its own advice in the page"""
    out, glyphs = [], []
    for line in text.splitlines():
        m = re.search(r"\[reels_lib\] font (.+?) not found", line)
        if m:
            out.append({"kind": "font", "text": f"這台電腦找不到字型「{m.group(1).strip()}」，樣張先用預設的 jf open 粉圓代替。"})
        elif "no logo.png" in line:
            out.append({"kind": "other", "text": "結尾卡選了「我的 logo」，但還沒有上傳 logo，樣張先用播放圖示代替。請在「結尾卡」上傳一張 logo。"})
        elif "variable font" in line:
            out.append({"kind": "other", "text": "這個字型用檔名載入會變得很細，請在「字型」改選它的字型名稱。"})
        elif "缺字" in line and "⚠" in line:
            glyphs.append(line.strip().lstrip("⚠").strip())
        elif glyphs and re.match(r"\s+\S\s+\(U\+", line):
            glyphs.append(line.strip())
    if glyphs: out.append({"kind": "glyph", "text": "\n".join(glyphs)})
    return out


FONT_CACHE = {}

def fonts():
    if "list" not in FONT_CACHE:
        sheet = os.path.join(TMP, "fonts_sheet.png")
        code, text = run_py(["fonts.py", "list", sheet, "--all"])   # every font; the page groups them by glyph forms
        items = []
        for m in re.finditer(r"^\s*\d+\.\s+(.+?)（(.+?)）\s+粗細:\s*(.*)$", text, re.M):
            ws = [int(x) for x in re.findall(r"\d+", m.group(3))]
            items.append({"name": m.group(1).strip(), "region": m.group(2), "weights": ws})
        code2, free = run_py(["fonts.py", "free"])
        free_items = []
        for line in free.splitlines():
            parts = [p.strip() for p in line.lstrip("- ").split("｜")]
            if line.startswith("- ") and len(parts) == 4:
                free_items.append(dict(zip(("name", "look", "license", "url"), parts)))
        FONT_CACHE["list"] = {"fonts": items, "free": free_items,
                              "sheet": file_url(sheet) if os.path.exists(sheet) else None,
                              "error": None if items else text[-800:]}
    return FONT_CACHE["list"]


# ---------------- project folders ----------------
def file_url(p):
    return f"/file?t={TOKEN}&p={quote(os.path.abspath(p))}"

def recent_projects():
    return [p for p in state().get("recent", []) if os.path.isdir(p)]

def caption_from_md(md, n):
    """the first code block under a heading that names 片段N (studio-caption-writer's format)"""
    heads = list(re.finditer(r"^(#{1,4})\s+(.*)$", md, re.M))
    for i, h in enumerate(heads):
        if re.search(r"片段\s*" + str(n) + r"(?!\d)", h.group(2)):
            end = next((x.start() for x in heads[i + 1:] if len(x.group(1)) <= len(h.group(1))), len(md))
            block = re.search(r"```[^\n]*\n(.*?)\n```", md[h.end():end], re.S)
            return block.group(1).strip() if block else md[h.end():end].strip()
    return None

def scan_project(folder):
    folder = os.path.abspath(clean_path(folder))
    try:
        names = sorted(os.listdir(folder))
    except OSError as e:
        raise ValueError(friendly_os_error(e, folder))
    problems = []
    rec = [folder] + [p for p in recent_projects() if os.path.normcase(p) != os.path.normcase(folder)]
    save_state(recent=rec[:8])
    # people often keep the recording in a subfolder (e.g. 原始素材\), so material, transcripts, scripts, picks and
    # captions are also looked up one level down, as relative paths; the toolkit's own folders are not material
    deep = list(names)
    for d in names:
        if d in ("_reels_work", "發文包") or d.startswith((".", "_")) or not os.path.isdir(os.path.join(folder, d)): continue
        try: deep += [os.path.join(d, n) for n in sorted(os.listdir(os.path.join(folder, d)))]
        except OSError: pass
    def has(suffix): return [n for n in deep if n.endswith(suffix)]
    captions = [n for n in deep if re.search(r"_Reels_\w*文案\.md$", n)]   # _Reels_文案.md, older _Reels_IG文案.md
    sources = [n for n in deep if n.lower().endswith(SOURCE_EXT) and "_Reels_" not in os.path.basename(n)]
    clips = []
    for n in names:
        m = re.match(r"(.+)_Reels_片段(\d+)\.mp4$", n)
        if not m: continue
        prefix, k = m.group(1), int(m.group(2))
        pack = os.path.join(folder, "發文包", f"片段{k}")
        cap, cap_src = None, None
        txt = os.path.join(pack, "caption.txt")
        if os.path.exists(txt):
            cap = try_read(read_text, txt, "utf-8-sig", problems=problems)
            cap_src = "發文包" if cap else None
        if not cap:
            for c in sorted((c for c in captions if os.path.basename(c).startswith(prefix + "_Reels_")),
                            key=lambda c: os.path.basename(c) != f"{prefix}_Reels_文案.md"):
                md = try_read(read_text, os.path.join(folder, c), problems=problems)
                cap = caption_from_md(md, k) if md else None
                if cap: break
            cap_src = "文案檔" if cap else None
        cover = os.path.join(pack, "cover_9x16.jpg")
        size = try_read(os.path.getsize, os.path.join(folder, n), problems=problems)
        clips.append({"name": n, "n": k, "prefix": prefix, "video": file_url(os.path.join(folder, n)),
                      "path": os.path.join(folder, n), "cover": file_url(cover) if os.path.exists(cover) else None,
                      "caption": cap.strip() if cap else None, "caption_from": cap_src,
                      "size_mb": round(size / 1e6, 1) if size is not None else None})
    clips.sort(key=lambda c: (c["prefix"], c["n"]))
    steps = [
        # a transcript or a finished clip means the material exists, even if it sits deeper than we look
        {"key": "source", "label": "素材（錄音、影片或口播稿）",
         "done": bool(sources or has("_口播稿.md") or has("_逐字稿.txt") or clips),
         "files": sources + has("_口播稿.md")},
        {"key": "transcript", "label": "逐字稿", "done": bool(has("_逐字稿.txt")), "files": has("_逐字稿.txt")},
        {"key": "picks", "label": "精華片段（長素材才需要）", "done": bool(has("_Reels精華片段.md")), "files": has("_Reels精華片段.md"),
         "optional": True},
        {"key": "videos", "label": "剪好的影片", "done": bool(clips), "files": [c["name"] for c in clips]},
        {"key": "captions", "label": "貼文文案", "done": bool(captions), "files": captions},
        {"key": "pack", "label": "發文包", "done": os.path.exists(os.path.join(folder, "發文包", "發文清單.md")),
         "files": ["發文包\\發文清單.md"] if os.path.exists(os.path.join(folder, "發文包", "發文清單.md")) else []},
    ]
    if clips and not problems:            # a listing can come from Windows' cache after a disk drops: probe one file
        try_read(lambda p: open(p, "rb").read(16), clips[0]["path"], problems=problems)
    picks_md = has("_Reels精華片段.md")
    md = try_read(read_text, os.path.join(folder, picks_md[0]), problems=problems) if picks_md else None
    return {"folder": folder, "steps": steps, "clips": clips, "recent": rec[:8], "problems": problems,
            "sources": sources, "scripts": has("_口播稿.md"), "project": read_project(folder),
            "picks": parse_picks(md) if md else [], "picks_file": picks_md[0] if picks_md else None}


# ---------------- per-folder project settings (_reels_studio.json; Claude and reels_lib read it) ----------------
PROJECT_FILE = "_reels_studio.json"

def check_project(folder):
    folder = os.path.abspath(clean_path(folder))
    if not any(os.path.normcase(folder) == os.path.normcase(p) for p in recent_projects()):
        raise ValueError("請先在「做影片」開啟這個資料夾")
    return folder

def read_project(folder):
    return read_json(os.path.join(folder, PROJECT_FILE), {}) or {}

def brand_ref(d):
    """how a channel folder is written in the project file: its folder name when it sits in the toolkit"""
    return os.path.basename(d) if os.path.normcase(os.path.dirname(os.path.abspath(d))) == os.path.normcase(HERE) else d

def save_project(body):
    folder = check_project(body["folder"])
    p = read_project(folder)
    if "brand" in body:
        p["brand"] = brand_ref(check_brand_dir(body["brand"]))
    if "source" in body:
        src = os.path.normpath(body["source"]) if body["source"] else ""      # a file name, or 子資料夾\檔名
        if src and (os.path.isabs(src) or src.startswith("..") or not os.path.isfile(os.path.join(folder, src))):
            raise ValueError("找不到這個素材檔")
        p["source"] = src or None
    if "count" in body:
        p["count"] = max(1, min(10, int(body["count"] or 3)))
    if "face" in body:
        p["face"] = "no" if body["face"] == "no" else "auto"
    if "notes" in body:
        p["notes"] = (body["notes"] or "").strip()[:2000]
    if "picks" in body:
        items = [{"n": int(x["n"]), "title": " ".join(str(x.get("title", "")).split())[:80]} for x in body["picks"]]
        p["picks"] = {"confirmed": bool(items), "items": items, "updated": time.strftime("%Y-%m-%d %H:%M")}
    p["updated"] = time.strftime("%Y-%m-%d %H:%M")
    p["_說明"] = "Reels Studio 控制台寫的這個資料夾的設定；Claude 開工時會照這裡做。"
    try:
        write_text(os.path.join(folder, PROJECT_FILE), json.dumps(p, ensure_ascii=False, indent=2) + "\n")
    except OSError as e:
        raise ValueError(friendly_os_error(e, folder))
    return p

def parse_picks(md):
    """the clip picker's sections: ## 片段 N｜主題 / **時間碼：…** / transcript / **為什麼適合：** bullets / **建議標題：** …"""
    out = []
    heads = list(re.finditer(r"^##\s*片段\s*(\d+)\s*[｜|]\s*(.*)$", md, re.M))
    for i, h in enumerate(heads):
        nxt = re.search(r"^## ", md[h.end():], re.M)
        body = md[h.end():h.end() + nxt.start()] if nxt else md[h.end():]
        tm = re.search(r"時間碼[：:]\s*(.+?)(?:\*\*|$)", body, re.M)
        title = re.search(r"\*\*建議標題[：:]\*\*\s*(.+)", body)
        why = re.search(r"\*\*為什麼適合[：:]\*\*(.*?)(?=\n\*\*建議標題|\Z)", body, re.S)
        start = tm.end() if tm else 0
        text = body[start:why.start() if why else len(body)]
        text = re.sub(r"\*\*", "", text).strip()
        out.append({"n": int(h.group(1)), "topic": h.group(2).strip(), "time": tm.group(1).strip() if tm else "",
                    "title": title.group(1).strip() if title else "",
                    "why": [re.sub(r"\*\*", "", l).strip("-• ").strip() for l in (why.group(1) if why else "").splitlines() if l.strip()],
                    "text": text[:1500]})
    return out


def projects_using(d):
    """recently opened project folders whose _reels_studio.json picks this channel"""
    refs = {os.path.normcase(brand_ref(d)), os.path.normcase(os.path.abspath(d))}
    return [p for p in recent_projects() if os.path.normcase(str(read_project(p).get("brand") or "")) in refs]

def to_recycle_bin(path):
    """move a folder to the Windows Recycle Bin (so the user can restore it); False if the shell refused"""
    import ctypes
    from ctypes import wintypes
    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR), ("pTo", wintypes.LPCWSTR),
                    ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL), ("hNameMappings", ctypes.c_void_p),
                    ("lpszProgressTitle", wintypes.LPCWSTR)]
    FO_DELETE, FOF_SILENT, FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_NOERRORUI = 3, 0x4, 0x10, 0x40, 0x400
    op = SHFILEOPSTRUCTW(None, FO_DELETE, os.path.abspath(path) + "\0", None,
                         FOF_SILENT | FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_NOERRORUI, False, None, None)
    return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) == 0 and not op.fAnyOperationsAborted and not os.path.exists(path)

def delete_brand(body):
    d = check_brand_dir(body["dir"])
    if os.path.normcase(os.path.abspath(d)) == os.path.normcase(os.path.join(HERE, "my-brand")):
        raise ValueError("預設風格不能刪除：沒有選風格的資料夾都會用它。想重來的話，直接修改它的設定就好。")
    if os.environ.get("REELS_BRAND") and os.path.normcase(os.path.abspath(os.environ["REELS_BRAND"])) == os.path.normcase(os.path.abspath(d)):
        raise ValueError("這個風格是用環境變數 REELS_BRAND 指定的，請先移除那個設定再刪除。")
    if not os.path.isdir(d): raise ValueError("這個風格已經不存在了")
    used = projects_using(d)
    where = "資源回收筒"
    if not to_recycle_bin(d):                     # e.g. a drive without a Recycle Bin: keep a copy beside the toolkit
        keep = os.path.join(HERE, "_已刪除的風格", f"{os.path.basename(d)}-{time.strftime('%Y%m%d-%H%M%S')}")
        os.makedirs(os.path.dirname(keep), exist_ok=True)
        shutil.move(d, keep); where = keep
    if os.path.normcase(state().get("brand") or "") == os.path.normcase(d): save_state(brand=os.path.join(HERE, "my-brand"))
    for p in used:                                # as promised in the confirmation: those folders go back to the default
        pj = read_project(p); pj.pop("brand", None)
        try: write_text(os.path.join(p, PROJECT_FILE), json.dumps(pj, ensure_ascii=False, indent=2) + "\n")
        except OSError as e: print("could not update", p, repr(e))
    return {"ok": True, "where": where, "projects": used}


def logo_url(d):
    p = os.path.join(d, "logo.png")
    return file_url(p) + f"&v={int(os.path.getmtime(p))}" if os.path.exists(p) else None


def save_logo(body):
    """an uploaded image (data URL; PNG / JPG / WEBP / GIF) -> <channel>/logo.png, at most 1000 px on its long side"""
    import base64, io
    d = check_brand_dir(body["dir"])
    data = body.get("data") or ""
    if "," not in data: raise ValueError("沒有收到圖片")
    raw = base64.b64decode(data.split(",", 1)[1])
    if len(raw) > 20e6: raise ValueError("圖片太大了（超過 20 MB），請換一張小一點的")
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)); im.load()
    except Exception:
        raise ValueError("讀不到這張圖片，請用 PNG、JPG 或 WEBP 檔")
    im = im.convert("RGBA")
    im.thumbnail((1000, 1000))
    alpha = im.getchannel("A")
    transparent = sum(alpha.resize((40, 40)).histogram()[:20]) > 40   # more than 2.5% of it is see-through
    os.makedirs(d, exist_ok=True)
    im.save(os.path.join(d, "logo.png"))
    return {"logo": logo_url(d), "transparent": transparent, "size": im.size}


def new_brand(body):
    """make my-brand-<name>; blank, or reusing another channel's look (brand.json + the free style's direction; the rest
    of BRAND.md starts blank)"""
    name = " ".join((body.get("name") or "").split())
    if not name: raise ValueError("請輸入新風格的名稱")
    slug = re.sub(r'[<>:"/\\|?*\s.]+', "-", name).strip("-") or "channel"
    d = os.path.join(HERE, "my-brand-" + slug); k = 2
    while os.path.exists(d): d = os.path.join(HERE, f"my-brand-{slug}-{k}"); k += 1
    src = load_brand(check_brand_dir(body["copy_from"])) if body.get("copy_from") else None
    look = src["brand"] if src else json.loads(json.dumps(BRAND_DEFAULTS))
    os.makedirs(d)
    e = look.get("end_card") or {}
    style = (look.get("style") or {}) if src else {"preset": "free"}   # a blank channel starts as 自由創作
    # the free style's direction belongs to the look, so it comes along; the rest of BRAND.md starts blank
    fields = {k: src["fields"][k] for k in ("自由創作方向", "參考帳號或影片") if src and src["fields"].get(k)}
    form = {"dir": d, "fields": fields, "brand": {
        "name": name, "tag": "", "palette": look.get("palette", "cream"), "colors": look.get("colors") or {},
        "font": look.get("font"), "font_weight": look.get("font_weight"), "speaker_label": look.get("speaker_label", "主持人"),
        "end_card": {k: e.get(k, "") for k in ("icon", "badge", "cta", "sub", "guest_prefix", "logo_shape")},
        "style": resolved_style(style) | {"preset": style.get("preset", "handmade")},
        "layout": resolved_layout(look.get("layout"))}}
    if body.get("copy_from"):                     # keep every colour override, not only accent/highlight, and the logo
        if os.path.exists(os.path.join(body["copy_from"], "logo.png")): shutil.copy2(os.path.join(body["copy_from"], "logo.png"), os.path.join(d, "logo.png"))
        write_text(os.path.join(d, "brand.json"), json.dumps({"colors": look.get("colors") or {}}, ensure_ascii=False))
    save_brand(form)
    for fn in ("brand.json.bak", "BRAND.md.bak"):
        if os.path.exists(os.path.join(d, fn)): os.remove(os.path.join(d, fn))
    return d


def pick_folder():
    code = ("import tkinter as tk\nfrom tkinter import filedialog\nr = tk.Tk(); r.withdraw(); r.attributes('-topmost', True)\n"
            "print(filedialog.askdirectory(title='選擇素材所在的資料夾') or '')")
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=600, creationflags=NO_WINDOW,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return os.path.normpath(p.stdout.decode("utf-8", "replace").strip()) if p.stdout.strip() else ""


def _top_windows():
    """visible titled top-level windows: {hwnd: title}"""
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32
    out = {}
    def cb(hwnd, _):
        if u.IsWindowVisible(hwnd):
            n = u.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1); u.GetWindowTextW(hwnd, buf, n + 1); out[hwnd] = buf.value
        return True
    u.EnumWindows(ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(cb), 0)
    return out

def _launch_in_front(launch, title_hint):
    """Run launch() and bring the window it opens to the front. The panel runs in the background (pythonw, no window),
    so Windows opens Explorer / Notepad *behind* the browser and the click looks like it did nothing. Find the new
    window (or one whose title has title_hint, e.g. an Explorer window that was already open) and raise it; a
    synthetic key press first makes Windows accept SetForegroundWindow from this process."""
    try:
        before = _top_windows()
    except Exception:
        return launch()
    launch()
    try:
        import ctypes
        u = ctypes.windll.user32
        for _ in range(30):                     # up to ~3 s for the window to appear
            time.sleep(0.1)
            now = _top_windows()
            new = [h for h in now if h not in before]
            hit = new or [h for h, t in now.items() if title_hint and title_hint in t]
            if hit:
                hwnd = hit[0]
                if u.IsIconic(hwnd): u.ShowWindow(hwnd, 9)          # SW_RESTORE
                u.keybd_event(0x87, 0, 0, 0); u.keybd_event(0x87, 0, 2, 0)   # F24 down / up: no app reacts to it
                u.SetForegroundWindow(hwnd)
                return
    except Exception as e:                      # opening worked; only raising it failed
        print("could not bring the window to the front:", repr(e))

def open_path(p, reveal=False):
    """open a folder in Explorer, show a file in its folder, or open a channel's BRAND.md — nothing else"""
    p = os.path.abspath(clean_path(p))
    if reveal and os.path.isfile(p) and under(p, recent_projects()):
        return _launch_in_front(lambda: subprocess.Popen(["explorer", "/select,", p]), os.path.basename(os.path.dirname(p)))
    if os.path.isdir(p) and (under(p, recent_projects()) or under(p, brand_dirs())):
        return _launch_in_front(lambda: os.startfile(p), os.path.basename(p))
    if os.path.basename(p) in ("BRAND.md", "brand.json") and under(p, brand_dirs()) and os.path.exists(p):
        return _launch_in_front(lambda: subprocess.Popen(["notepad", p]), os.path.basename(p))
    raise ValueError("這個位置不能從控制台打開")


# ---------------- HTTP ----------------
class Handler(BaseHTTPRequestHandler):
    server_version = "ReelsStudio"

    def log_message(self, fmt, *args):
        pass

    def host_ok(self):           # blocks DNS-rebinding: only our own address
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def send(self, code, body, ctype="application/json; charset=utf-8", extra=None):
        if isinstance(body, (dict, list)): body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str): body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items(): self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)

    def do_GET(self):
        if not self.host_ok(): return self.send(403, {"error": "forbidden"})
        u = urlparse(self.path); q = parse_qs(u.query)
        if u.path == "/":
            html = INDEX_HTML.replace("__TOKEN__", TOKEN)
            return self.send(200, html, "text/html; charset=utf-8")
        if u.path in ("/icon.ico", "/favicon.ico"):
            return self.send(200, open(os.path.join(UI_DIR, "icon.ico"), "rb").read(), "image/x-icon")
        if u.path == "/guide":
            p = os.path.join(HERE, "使用說明.html")
            if not os.path.exists(p): return self.send(404, "還沒有使用說明，請重新執行安裝程式。", "text/plain; charset=utf-8")
            return self.send(200, open(p, encoding="utf-8").read(), "text/html; charset=utf-8")
        if unquote(u.path).startswith("/說明圖片/"):          # the guide's screenshots (relative to /guide)
            name = os.path.basename(unquote(u.path))
            p = os.path.join(HERE, "說明圖片", name)
            if not name.lower().endswith(".png") or not os.path.isfile(p): return self.send(404, {"error": "not found"})
            return self.send(200, open(p, "rb").read(), "image/png")
        if u.path == "/api/ping":
            return self.send(200, {"app": APP_ID, "version": VERSION})
        if u.path == "/file":
            if q.get("t", [""])[0] != TOKEN: return self.send(403, {"error": "token"})
            return self.send_file(q.get("p", [""])[0])
        return self.send(404, {"error": "not found"})

    do_HEAD = do_GET

    def send_file(self, p):
        p = os.path.abspath(p)
        ext = os.path.splitext(p)[1].lower()
        if ext not in MEDIA_EXT or not under(p, [TMP, HERE] + recent_projects()):
            return self.send(404, {"error": "not found"})
        try:                                        # open first: an unplugged disk fails here, before any header
            f = open(p, "rb"); size = os.fstat(f.fileno()).st_size
        except FileNotFoundError:
            return self.send(404, {"error": "not found"})
        except OSError as e:
            return self.send(503, {"error": friendly_os_error(e, p)})
        with f: self.stream(f, size, ext)

    def stream(self, f, size, ext):
        start, end = 0, size - 1
        rng = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
        if rng and (rng.group(1) or rng.group(2)):
            if rng.group(1): start = int(rng.group(1)); end = int(rng.group(2)) if rng.group(2) else size - 1
            else: start = max(0, size - int(rng.group(2)))
            end = min(end, size - 1)
            if start > end: return self.send(416, b"", extra={"Content-Range": f"bytes */{size}"})
        self.send_response(206 if rng and (rng.group(1) or rng.group(2)) else 200)
        self.send_header("Content-Type", MEDIA_EXT[ext])
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(end - start + 1))
        if rng and (rng.group(1) or rng.group(2)): self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if self.command == "HEAD": return
        f.seek(start); left = end - start + 1
        try:
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk: break
                self.wfile.write(chunk); left -= len(chunk)
        except OSError:                             # viewer closed the tab or seeked, or the disk dropped mid-way
            pass

    def do_POST(self):
        global last_ping
        if not self.host_ok() or self.headers.get("X-Token") != TOKEN:   # custom header: other sites cannot send it
            return self.send(403, {"error": "forbidden"})
        last_ping = time.time()
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0) or 0)) or b"{}")
            path = urlparse(self.path).path
            if path == "/api/state":
                st = state()
                brands = [load_brand(d) for d in brand_dirs()]
                cur = st.get("brand") if st.get("brand") in [b["dir"] for b in brands] else brands[0]["dir"]
                out = {"brands": brands, "current": cur, "palettes": PALETTES, "recent": recent_projects(),
                       "style_options": STYLE_OPTIONS, "style_presets": STYLE_PRESETS, "layout_options": LAYOUT_OPTIONS,
                       "layout_defaults": BRAND_DEFAULTS["layout"], "version": app_version(),
                       "welcomed": bool(st.get("welcomed")),     # the first-open welcome screen was seen
                       "studio": HERE, "env_brand": os.environ.get("REELS_BRAND")}
            elif path == "/api/ping": out = {"ok": True}
            elif path == "/api/latest": out = latest_release()
            elif path == "/api/fonts": out = fonts()
            elif path == "/api/preview": out = preview(body)
            elif path == "/api/save":
                save_brand(body); save_state(brand=body["dir"])
                out = dict(preview(body, real=True), saved=True, brand=load_brand(body["dir"]))
            elif path == "/api/welcomed": save_state(welcomed=True); out = {"ok": True}
            elif path == "/api/select-brand": check_brand_dir(body["dir"]); save_state(brand=body["dir"]); out = {"ok": True}
            elif path == "/api/pick-folder": out = {"path": pick_folder()}
            elif path == "/api/project": out = scan_project(body["path"])
            elif path == "/api/project-save": out = save_project(body)
            elif path == "/api/brand-usage": out = {"projects": projects_using(check_brand_dir(body["dir"]))}
            elif path == "/api/delete-brand": out = delete_brand(body)
            elif path == "/api/logo": out = save_logo(body)
            elif path == "/api/new-brand":
                d = new_brand(body); save_state(brand=d)
                out = dict(preview({"dir": d}, real=True), brand=load_brand(d))
            elif path == "/api/open": open_path(body["path"], body.get("reveal", False)); out = {"ok": True}
            elif path == "/api/quit":
                self.send(200, {"ok": True}); threading.Thread(target=self.server.shutdown, daemon=True).start(); return
            else: return self.send(404, {"error": "not found"})
            self.send(200, out)
        except ValueError as e:
            self.send(400, {"error": str(e)})
        except OSError as e:
            print("os error:", repr(e)); self.send(400, {"error": friendly_os_error(e)})
        except Exception as e:
            print("error:", repr(e)); self.send(500, {"error": f"{type(e).__name__}: {e}"})


def running_version(port):
    """version of a Reels Studio panel already on this port ('' for versions before it was reported), None if none"""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1) as r:
            j = json.loads(r.read())
            return j.get("version", "") if j.get("app") == APP_ID else None
    except Exception:
        return None


def stop_running(port):
    """ask an older panel to quit: its page carries its token, and only this machine can fetch that page"""
    import urllib.request
    try:
        page = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2).read().decode("utf-8", "replace")
        tok = re.search(r'const TOKEN = "([^"]+)"', page).group(1)
        urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/api/quit", b"{}", {"X-Token": tok}), timeout=2)
    except Exception as e:
        print("could not stop the old panel:", repr(e))
    for _ in range(25):                           # wait until the port is free again
        if running_version(port) is None: return True
        time.sleep(0.2)
    return False


_latest = {"at": 0, "out": None}
def latest_release():
    """the newest release on GitHub, read from where releases/latest redirects (…/tag/v1.5.0); no API key, no
    rate limit. Asked when the page opens, kept for an hour. Offline or GitHub down → {"latest": None}, not kept,
    and the page shows nothing"""
    import urllib.request
    if _latest["out"] and time.time() - _latest["at"] < 3600: return _latest["out"]
    try:
        req = urllib.request.Request(RELEASES + "/latest", method="HEAD", headers={"User-Agent": "ReelsStudio/" + app_version()})
        with urllib.request.urlopen(req, timeout=5) as r: m = re.search(r"/tag/v?(\d+(?:\.\d+)*)$", r.geturl())
    except Exception: m = None
    if not m: return {"latest": None}
    ver = lambda v: tuple(int(x) for x in re.findall(r"\d+", v))
    cur, new = app_version(), m.group(1)
    out = {"latest": new, "current": cur, "newer": bool(cur) and ver(new) > ver(cur),
           "notes": f"{RELEASES}/tag/v{new}", "download": f"{RELEASES}/latest/download/ReelsStudio.zip"}
    _latest.update(at=time.time(), out=out)
    return out


def main():
    args = sys.argv[1:]
    port = int(args[args.index("--port") + 1]) if "--port" in args else 8765
    browser = "--no-browser" not in args
    old = running_version(port)
    if old == VERSION:
        if browser: webbrowser.open(f"http://127.0.0.1:{port}/")
        return
    if old is not None:                           # updated since that one started (reinstall): replace it
        print(time.strftime("%Y-%m-%d %H:%M:%S"), f"replacing older panel ({old or 'unversioned'})")
        stop_running(port)
    srv = None
    for p in range(port, port + 20):
        try: srv = ThreadingHTTPServer(("127.0.0.1", p), Handler); break
        except OSError: continue
    if srv is None: sys.exit("沒有可用的連接埠")
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(time.strftime("%Y-%m-%d %H:%M:%S"), "Reels Studio 控制台:", url)

    def idle_watch():
        while True:
            time.sleep(30)
            if time.time() - last_ping > IDLE_EXIT: srv.shutdown(); return
    threading.Thread(target=idle_watch, daemon=True).start()
    if browser: webbrowser.open(url)
    try: srv.serve_forever()
    finally: shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
