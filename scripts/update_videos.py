#!/usr/bin/env python3
"""Refresh videos.json from the public YouTube RSS feed of @criscalin.

No API key. Runs daily from .github/workflows/update-videos.yml.
- Shorts go to "shorts" (newest first), long videos to "long".
- Older entries already in videos.json are kept (the feed shows only the latest 15).
- If YouTube cannot be reached, the file is left unchanged.
"""
import json, re, sys, urllib.request, urllib.error
import xml.etree.ElementTree as ET
from pathlib import Path

HANDLE = "criscalin"
OUT = Path(__file__).resolve().parent.parent / "videos.json"
UA = {"User-Agent": "Mozilla/5.0 (criscalin.com video sync)", "Accept-Language": "en",
      "Cookie": "CONSENT=YES+1; SOCS=CAI"}  # skip the EU consent page
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
ID_RE = re.compile(r"^[\w-]{6,20}$")


def get(url, method="GET"):
    req = urllib.request.Request(url, headers=UA, method=method)
    return urllib.request.urlopen(req, timeout=30)


def channel_id(known):
    if known and known.startswith("UC"):
        return known
    html = get(f"https://www.youtube.com/@{HANDLE}").read().decode("utf-8", "replace")
    for pat in (r'"externalId":"(UC[\w-]{22})"', r'"channelId":"(UC[\w-]{22})"',
                r'channel/(UC[\w-]{22})'):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    raise RuntimeError("channel id not found on the @%s page" % HANDLE)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def is_short(vid):
    """YouTube serves /shorts/<id> with 200 for Shorts and redirects long videos to /watch."""
    opener = urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(urllib.request.Request(f"https://www.youtube.com/shorts/{vid}", headers=UA), timeout=30)
        return r.status == 200
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            return False
        raise


def parse_feed(xml_bytes):
    root = ET.fromstring(xml_bytes)
    out = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", default="", namespaces=NS)
        if not ID_RE.match(vid):
            continue
        out.append({"id": vid,
                    "title": (e.findtext("a:title", default="", namespaces=NS) or "").strip(),
                    "published": e.findtext("a:published", default="", namespaces=NS)[:10]})
    return out


def merge(fresh, old):
    seen, res = set(), []
    for v in fresh + old:
        if v.get("id") in seen or not ID_RE.match(v.get("id", "")):
            continue
        seen.add(v["id"])
        res.append(v)
    res.sort(key=lambda v: v.get("published", ""), reverse=True)  # undated (old) entries sink
    return res


def main():
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    try:
        cid = channel_id(data.get("channel_id"))
        feed = parse_feed(get(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}").read())
    except Exception as exc:  # network or YouTube change: keep the site as it is
        print("YouTube not reachable, videos.json unchanged:", exc, file=sys.stderr)
        return 0
    known_short = {v["id"] for v in data.get("shorts", [])}
    known_long = {v["id"] for v in data.get("long", [])}
    shorts, longs = [], []
    for v in feed:
        if v["id"] in known_short:
            kind = True
        elif v["id"] in known_long:
            kind = False
        else:
            try:
                kind = is_short(v["id"])
            except Exception as exc:
                print("skip", v["id"], exc, file=sys.stderr)
                continue
        (shorts if kind else longs).append(v)
    new = {
        "youtube_channel": data.get("youtube_channel", "https://www.youtube.com/@criscalin"),
        "instagram": data.get("instagram", "https://www.instagram.com/iamcriscalin"),
        "channel_id": cid,
        "shorts": merge(shorts, data.get("shorts", [])),
        "long": merge(longs, data.get("long", [])),
    }
    text = json.dumps(new, ensure_ascii=False, indent=1) + "\n"
    if OUT.exists() and OUT.read_text(encoding="utf-8") == text:
        print("no change")
    else:
        OUT.write_text(text, encoding="utf-8")
        print(f"updated: {len(new['shorts'])} shorts, {len(new['long'])} long")
    return 0


if __name__ == "__main__":
    sys.exit(main())
