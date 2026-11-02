# Reels Studio：Mac 安裝用的複製程式（給 Claude 依照 INSTALL_MAC.md 執行，做的事跟 install.ps1 的第 1 步一樣）
# 用法：python3.13 mac_copy.py "<解壓縮出來的 程式檔（不用打開） 資料夾>" [<測試用的家目錄，預設 ~>]
# 把 agents、skill、工具包複製到 ~/.claude/，{{STUDIO}}、{{HOME}} 換成這台 Mac 的路徑，路徑裡的 \ 一起換成 /。
# 可重複執行：會被覆蓋的舊檔先備份；頻道設定（reels-studio/my-brand*/）不會被動到。
import os, re, shutil, sys, time
SRC = os.path.abspath(sys.argv[1])
HOME = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.expanduser("~")
CLAUDE = os.path.join(HOME, ".claude")
STUDIO = os.path.join(CLAUDE, "reels-studio")
PARTS = [("claude/agents", "agents"), ("claude/skills/reels-studio", "skills/reels-studio"), ("claude/reels-studio", "reels-studio")]
BACKUP = os.path.join(CLAUDE, "backup-reels-studio-" + time.strftime("%Y%m%d-%H%M%S"))
TOKEN = re.compile(r"\{\{(STUDIO|HOME)\}\}((?:\\[^\\\s\"'`)]+)*\\?)")

def fix(text):
    return TOKEN.sub(lambda m: (STUDIO if m.group(1) == "STUDIO" else HOME) + m.group(2).replace("\\", "/"), text)

def skip(rel, name):
    parts = rel.split(os.sep)
    return (name == "ui_state.json" or os.path.splitext(name)[1] in (".pyc", ".bak", ".log")
            or any(p == "__pycache__" or p.startswith("my-brand") for p in parts))

for frm, to in PARTS:
    src_dir = os.path.join(SRC, frm)
    for d, _, names in os.walk(src_dir):
        for n in names:
            src = os.path.join(d, n)
            rel = os.path.relpath(src, src_dir)
            if skip(rel, n): continue
            dst = os.path.join(CLAUDE, to, rel)
            if os.path.exists(dst):
                bk = os.path.join(BACKUP, to, rel)
                os.makedirs(os.path.dirname(bk), exist_ok=True); shutil.copy2(dst, bk)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.splitext(n)[1] in (".md", ".py", ".txt"):
                with open(src, encoding="utf-8") as f: text = f.read()
                with open(dst, "w", encoding="utf-8", newline="") as f: f.write(fix(text))
            else:
                shutil.copy2(src, dst)
    print("OK ", to)
if os.path.exists(BACKUP): print("舊檔已備份到", BACKUP)

ver = os.path.join(SRC, "VERSION")
if os.path.exists(ver):
    with open(ver, encoding="utf-8") as f: v = f.readline().strip()
    with open(os.path.join(STUDIO, "VERSION"), "w", encoding="utf-8") as f: f.write(v + "\n")

guide = os.path.join(os.path.dirname(SRC), "① 先看我.html")
if os.path.exists(guide):
    with open(guide, encoding="utf-8") as f: html = f.read()
    html = html.replace("程式檔（不用打開）\\font\\OFL.txt", "font/OFL.txt").replace("程式檔（不用打開）/說明圖片/", "說明圖片/")
    with open(os.path.join(STUDIO, "使用說明.html"), "w", encoding="utf-8") as f: f.write(html)
    shots = os.path.join(SRC, "說明圖片")
    if os.path.isdir(shots): shutil.copytree(shots, os.path.join(STUDIO, "說明圖片"), dirs_exist_ok=True)
os.makedirs(os.path.join(STUDIO, "font"), exist_ok=True)
shutil.copy2(os.path.join(SRC, "font", "OFL.txt"), os.path.join(STUDIO, "font", "OFL.txt"))
# 引擎只會到 Windows 的字型資料夾和工具包資料夾找字型檔，所以 Mac 上要在工具包資料夾放一份
shutil.copy2(os.path.join(SRC, "font", "jf-openhuninn-1.1.ttf"), os.path.join(STUDIO, "jf-openhuninn-1.1.ttf"))

left = []
for d, _, names in os.walk(CLAUDE):
    if "backup-reels-studio-" in d: continue
    for n in names:
        if n.endswith((".md", ".py")):
            p = os.path.join(d, n)
            t = open(p, encoding="utf-8", errors="replace").read()
            if "{{STUDIO}}" in t or "{{HOME}}" in t or re.search(re.escape(STUDIO) + r"\\", t): left.append(p)
print("路徑沒換好的檔案：", left or "沒有")
