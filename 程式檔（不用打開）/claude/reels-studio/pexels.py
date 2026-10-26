"""Pexels photo / video search + download for Reels B-roll.

The API key is read from the PEXELS_API_KEY environment variable (falls back to the Windows user
environment in the registry, set with `setx`). The key is never printed.

usage:
  python pexels.py search photos "rainy window" <clipdir> [--n 8] [--orientation portrait|landscape|square]
  python pexels.py search videos "ocean waves" <clipdir> [--n 6] [--orientation portrait]
      -> prints numbered results and saves small previews to <clipdir>/assets/_previews/ (Read them to choose)
  python pexels.py get photo <id> <clipdir>
  python pexels.py get video <id> <clipdir>
      -> downloads to <clipdir>/assets/pexels_photo_<id>.jpg / pexels_video_<id>.mp4 and records the credit
         in <clipdir>/assets/credits.json + credits.txt
"""
import argparse, json, os, sys, urllib.parse, urllib.request

API = "https://api.pexels.com"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # photographer names can be any script


def api_key():
    k = os.environ.get("PEXELS_API_KEY")
    if not k and sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
                k = winreg.QueryValueEx(h, "PEXELS_API_KEY")[0]
        except OSError:
            k = None
    if not k:
        sys.exit("PEXELS_API_KEY is not set. Ask the user to run: setx PEXELS_API_KEY \"<their key>\" (never paste it in chat).")
    return k


def call(path, params):
    url = f"{API}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": api_key(), "User-Agent": "reels-studio/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "reels-studio/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        while True:
            b = r.read(1 << 16)
            if not b: break
            f.write(b)
    return path


def assets(clipdir):
    d = os.path.join(clipdir, "assets"); os.makedirs(os.path.join(d, "_previews"), exist_ok=True); return d


def record_credit(clipdir, entry):
    d = assets(clipdir); p = os.path.join(d, "credits.json")
    data = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []
    data = [e for e in data if not (e["type"] == entry["type"] and e["id"] == entry["id"])] + [entry]
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(d, "credits.txt"), "w", encoding="utf-8") as f:
        f.write("素材來源：Pexels（pexels.com）\n")
        for e in data:
            f.write(f"- {'照片' if e['type'] == 'photo' else '影片'} by {e['author']}：{e['url']}\n")


def search(kind, query, clipdir, n, orientation):
    d = assets(clipdir)
    if kind == "photos":
        res = call("/v1/search", {"query": query, "per_page": n, "orientation": orientation})
        for i, p in enumerate(res.get("photos", [])):
            prev = os.path.join(d, "_previews", f"photo_{p['id']}.jpg")
            download(p["src"]["medium"], prev)
            print(f"[{i}] photo id={p['id']} {p['width']}x{p['height']} by {p['photographer']} | {p.get('alt') or ''}\n     preview: {prev}")
    else:
        res = call("/videos/search", {"query": query, "per_page": n, "orientation": orientation})
        for i, v in enumerate(res.get("videos", [])):
            prev = os.path.join(d, "_previews", f"video_{v['id']}.jpg")
            download(v["image"], prev)
            print(f"[{i}] video id={v['id']} {v['width']}x{v['height']} {v['duration']}s by {v['user']['name']}\n     preview (first frame only, check more frames after download): {prev}")
    print(f"total results: {res.get('total_results')}")


def get(kind, pid, clipdir):
    d = assets(clipdir)
    if kind == "photo":
        p = call(f"/v1/photos/{pid}", {})
        # long side 2000 px: enough for a full-bleed 1080x1920 frame plus Ken Burns zoom
        dim = "h=2000" if p["height"] >= p["width"] else "w=2000"
        src = p["src"]["original"].split("?")[0] + f"?auto=compress&cs=tinysrgb&{dim}"
        out = download(src, os.path.join(d, f"pexels_photo_{pid}.jpg"))
        record_credit(clipdir, {"type": "photo", "id": pid, "author": p["photographer"], "url": p["url"]})
    else:
        v = call(f"/videos/videos/{pid}", {})
        files = [f for f in v["video_files"] if f.get("file_type") == "video/mp4" and f.get("width")]
        # prefer the smallest file that still covers 1080 px on the short side; else the largest available
        good = sorted([f for f in files if min(f["width"], f["height"]) >= 1080], key=lambda f: f["width"] * f["height"])
        pick = good[0] if good else max(files, key=lambda f: f["width"] * f["height"])
        out = download(pick["link"], os.path.join(d, f"pexels_video_{pid}.mp4"))
        record_credit(clipdir, {"type": "video", "id": pid, "author": v["user"]["name"], "url": v["url"]})
    print("saved", out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("kind", choices=["photos", "videos"]); s.add_argument("query"); s.add_argument("clipdir")
    s.add_argument("--n", type=int, default=8); s.add_argument("--orientation", default="portrait")
    g = sub.add_parser("get"); g.add_argument("kind", choices=["photo", "video"]); g.add_argument("id", type=int); g.add_argument("clipdir")
    a = ap.parse_args()
    if a.cmd == "search": search(a.kind, a.query, a.clipdir, a.n, a.orientation)
    else: get(a.kind, a.id, a.clipdir)


if __name__ == "__main__":
    main()
