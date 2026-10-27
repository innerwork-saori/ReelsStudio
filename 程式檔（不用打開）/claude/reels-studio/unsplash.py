"""Unsplash photo search + download for Reels B-roll (photos only: Unsplash has no videos).

The access key is read from the UNSPLASH_ACCESS_KEY environment variable (falls back to the Windows user
environment in the registry, set with `setx`). The key is never printed.

Unsplash API guidelines: every download is reported to Unsplash (links.download_location), and every photo
used must credit the photographer and Unsplash. `get` records that credit in credits.txt, shared with pexels.py.

usage:
  python unsplash.py search "rainy window" <clipdir> [--n 8] [--orientation portrait|landscape|square]
      -> prints numbered results and saves small previews to <clipdir>/assets/_previews/ (Read them to choose)
  python unsplash.py get <id> <clipdir>
      -> downloads to <clipdir>/assets/unsplash_photo_<id>.jpg and records the credit
         in <clipdir>/assets/credits.json + credits.txt
"""
import argparse, json, os, sys, urllib.parse, urllib.request

from pexels import assets, download, env_key, record_credit

API = "https://api.unsplash.com"
UTM = "utm_source=reels_studio&utm_medium=referral"    # Unsplash asks for these on every link back to it
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # photographer names can be any script


def api_key():
    k = env_key("UNSPLASH_ACCESS_KEY")
    if not k:
        sys.exit("UNSPLASH_ACCESS_KEY is not set. Ask the user to run: setx UNSPLASH_ACCESS_KEY \"<their key>\" (never paste it in chat).")
    return k


def call(url, params=None):
    if not url.startswith("http"): url = API + url
    if params: url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {api_key()}", "Accept-Version": "v1",
                                               "User-Agent": "reels-studio/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def with_utm(url):
    return url + ("&" if "?" in url else "?") + UTM


def search(query, clipdir, n, orientation):
    d = assets(clipdir)
    res = call("/search/photos", {"query": query, "per_page": min(n, 30), "content_filter": "high",
                                  "orientation": "squarish" if orientation == "square" else orientation})
    # Unsplash+ photos need a paid licence: skip them
    photos = [p for p in res.get("results", []) if not (p.get("premium") or p.get("plus"))]
    for i, p in enumerate(photos):
        prev = os.path.join(d, "_previews", f"unsplash_{p['id']}.jpg")
        download(p["urls"]["small"], prev)
        print(f"[{i}] photo id={p['id']} {p['width']}x{p['height']} by {p['user']['name']} | {p.get('alt_description') or ''}\n     preview: {prev}")
    print(f"total results: {res.get('total')}")


def get(pid, clipdir):
    d = assets(clipdir)
    p = call(f"/photos/{urllib.parse.quote(pid)}")
    if p.get("premium") or p.get("plus"):
        sys.exit(f"photo {pid} is Unsplash+ (paid licence): pick another one")
    # long side 2000 px: enough for a full-bleed 1080x1920 frame plus Ken Burns zoom
    dim = {"h": 2000} if p["height"] >= p["width"] else {"w": 2000}
    src = p["urls"]["raw"] + "&" + urllib.parse.urlencode({"fm": "jpg", "q": 85, **dim})
    out = download(src, os.path.join(d, f"unsplash_photo_{pid}.jpg"))
    call(p["links"]["download_location"])                  # required by the API guidelines: counts the download
    record_credit(clipdir, {"type": "photo", "id": pid, "source": "unsplash", "author": p["user"]["name"],
                            "author_url": with_utm(p["user"]["links"]["html"]), "url": with_utm(p["links"]["html"])})
    print("saved", out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("clipdir")
    s.add_argument("--n", type=int, default=8); s.add_argument("--orientation", default="portrait")
    g = sub.add_parser("get"); g.add_argument("id"); g.add_argument("clipdir")
    a = ap.parse_args()
    if a.cmd == "search": search(a.query, a.clipdir, a.n, a.orientation)
    else: get(a.id, a.clipdir)


if __name__ == "__main__":
    main()
