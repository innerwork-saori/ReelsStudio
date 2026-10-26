r"""Build the download zip for a GitHub release: dist/ReelsStudio.zip

usage: python tools/build_release.py

The zip holds the package files at its root (no wrapping folder), so Windows' "Extract All" gives
ReelsStudio\① 先看我.html, ② 雙擊安裝.bat, 程式檔（不用打開）\ — one level, exactly what the guide describes.
The asset name has no version, so https://github.com/<owner>/ReelsStudio/releases/latest/download/ReelsStudio.zip
always points at the newest release; the version is in 程式檔（不用打開）/VERSION and the release title.
"""
import os, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRAM = "程式檔（不用打開）"
TOP = ["① 先看我.html", "② 雙擊安裝.bat", PROGRAM]
SKIP_DIRS = {"__pycache__"}
SKIP_EXT = {".pyc", ".bak", ".log"}
SKIP_NAMES = {"ui_state.json"}


def files():
    for top in TOP:
        p = os.path.join(ROOT, top)
        if os.path.isfile(p):
            yield top
            continue
        for d, dirs, names in os.walk(p):
            dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith("my-brand"))
            for n in sorted(names):
                if os.path.splitext(n)[1].lower() in SKIP_EXT or n in SKIP_NAMES: continue
                yield os.path.relpath(os.path.join(d, n), ROOT)


def main():
    version = open(os.path.join(ROOT, PROGRAM, "VERSION"), encoding="utf-8").read().strip()
    bat = open(os.path.join(ROOT, "② 雙擊安裝.bat"), "rb").read()
    if b"\n" in bat.replace(b"\r\n", b""): sys.exit("② 雙擊安裝.bat must use CRLF line endings")
    if not bat.isascii(): sys.exit("② 雙擊安裝.bat must stay ASCII (cmd reads it in the system codepage)")
    if not open(os.path.join(ROOT, PROGRAM, "install.ps1"), "rb").read(3) == b"\xef\xbb\xbf":
        sys.exit("install.ps1 must keep its UTF-8 BOM (Windows PowerShell 5.1 reads it as ANSI otherwise)")
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    out = os.path.join(ROOT, "dist", "ReelsStudio.zip")
    n = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:   # non-ASCII names get the UTF-8 flag
        for rel in files():
            z.write(os.path.join(ROOT, rel), rel.replace(os.sep, "/")); n += 1
    print(f"v{version}: {n} files -> {out} ({os.path.getsize(out) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
