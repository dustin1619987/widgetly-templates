# Collects public-domain wallpapers for Widgetly: paintings and prints from the
# Art Institute of Chicago and the Met (works both mark as public domain) and
# NASA photos (public domain as US government works), each made into a
# 1080x2340 phone wallpaper. Writes wallpapers/*.webp, wallpapers/thumb/*.webp
# and wallpapers.json. Run by .github/workflows/pd-wallpapers.yml.
import io, json, os, re, time
import requests
from PIL import Image, ImageFilter, ImageEnhance

W, H = 1080, 2340
OUT = "wallpapers"
UA = {"User-Agent": "Widgetly wallpapers (github.com/dustin1619987/widgetly-templates)", "AIC-User-Agent": "Widgetly (github.com/dustin1619987/widgetly-templates)"}
PER_QUERY = 6
# Subjects kept out of a family-friendly wallpaper app.
AVOID = re.compile(r"nude|naked|bath|venus|crucif|martyr|dead|death|skull|battle|war\b|execution|wound|blood|hunt|slave|lynch|torture|erotic|bather|leda|susanna|judith|saint sebastian|massacre|corpse|funeral", re.I)

CATEGORIES = [
    ("Impressionist", [("aic", "monet"), ("aic", "renoir landscape"), ("aic", "pissarro"), ("aic", "sisley"), ("met", "monet")]),
    ("Japanese prints", [("aic", "hokusai"), ("aic", "hiroshige"), ("aic", "japanese woodblock landscape")]),
    ("Flowers", [("met", "flowers still life painting"), ("aic", "flowers painting"), ("met", "botanical")]),
    ("Landscapes", [("aic", "landscape painting"), ("met", "landscape hudson river"), ("aic", "seascape")]),
    ("Space", [("nasa", "nebula hubble"), ("nasa", "galaxy webb"), ("nasa", "star cluster")]),
    ("Earth & sky", [("nasa", "earth from space station"), ("nasa", "aurora from space"), ("nasa", "moon")]),
]

def get(url, **kw):
    for _ in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=40, **kw)
            if r.status_code == 200: return r
        except requests.RequestException: pass
        time.sleep(2)
    return None

def aic(q):
    r = get("https://api.artic.edu/api/v1/artworks/search", params={"q": q, "query[term][is_public_domain]": "true", "fields": "id,title,artist_title,image_id,is_public_domain,thumbnail", "limit": 40})
    for a in (r.json().get("data", []) if r else []):
        if not a.get("is_public_domain") or not a.get("image_id"): continue
        t = a.get("thumbnail") or {}
        if (t.get("width") or 0) < 400: continue
        yield dict(title=a["title"], artist=a.get("artist_title") or "Unknown artist",
                   url=f"https://www.artic.edu/iiif/2/{a['image_id']}/full/1686,/0/default.jpg",
                   source=f"https://www.artic.edu/artworks/{a['id']}", credit="Art Institute of Chicago", kind="art")

def met(q):
    r = get("https://collectionapi.metmuseum.org/public/collection/v1/search", params={"q": q, "hasImages": "true", "isPublicDomain": "true"})
    for oid in ((r.json().get("objectIDs") or [])[:60] if r else []):
        o = get(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
        if not o: continue
        o = o.json()
        if not o.get("isPublicDomain") or not o.get("primaryImage"): continue
        if o.get("classification") not in ("Paintings", "Prints", "Drawings", "Watercolors"): continue
        yield dict(title=o.get("title", ""), artist=o.get("artistDisplayName") or "Unknown artist", url=o["primaryImage"],
                   source=o.get("objectURL", ""), credit="The Metropolitan Museum of Art", kind="art")

def nasa(q):
    r = get("https://images-api.nasa.gov/search", params={"q": q, "media_type": "image"})
    for it in (r.json()["collection"]["items"] if r else [])[:60]:
        d = (it.get("data") or [{}])[0]
        who = " ".join(str(d.get(k, "")) for k in ("photographer", "secondary_creator", "description"))
        # Only NASA's own pictures: others' (credited, copyrighted) are left out.
        if re.search(r"©|copyright|courtesy of (?!nasa)|getty|reuters|\bAP\b", who, re.I): continue
        r2 = get(it["href"])
        if not r2: continue
        files = [u for u in r2.json() if re.search(r"~(orig|large)\.jpe?g$", u, re.I)]
        if not files: continue
        url = sorted(files, key=lambda u: "orig" not in u)[0].replace("http://", "https://")
        yield dict(title=d.get("title", ""), artist="NASA", url=url, source=f"https://images.nasa.gov/details/{d.get('nasa_id','')}", credit="NASA", kind="photo")

def make(img, kind):
    img = img.convert("RGB")
    ratio = img.height / img.width
    if kind == "photo" or ratio >= 1.3:
        # Fill the screen, trimming the sides (or top and bottom).
        s = max(W / img.width, H / img.height)
        img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
        x, y = (img.width - W) // 2, (img.height - H) // 2
        return img.crop((x, y, x + W, y + H))
    # Wide paintings stay whole, on a soft blur of themselves.
    s = max(W / img.width, H / img.height)
    back = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (back.width - W) // 2, (back.height - H) // 2
    back = back.crop((x, y, x + W, y + H)).filter(ImageFilter.GaussianBlur(40))
    back = ImageEnhance.Brightness(back).enhance(0.75)
    fw = int(W * 0.94); fh = round(img.height * fw / img.width)
    front = img.resize((fw, fh), Image.LANCZOS)
    back.paste(front, ((W - fw) // 2, int(H * 0.52 - fh / 2)))
    return back

def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:50]

def main():
    os.makedirs(f"{OUT}/thumb", exist_ok=True)
    old = {}
    if os.path.exists("wallpapers.json"):
        old = {w["id"]: w for w in json.load(open("wallpapers.json"))["wallpapers"]}
    found, seen = [], set(old)
    for category, queries in CATEGORIES:
        for source, q in queries:
            n = 0
            for item in {"aic": aic, "met": met, "nasa": nasa}[source](q):
                if n >= PER_QUERY: break
                if AVOID.search(item["title"]): continue
                wid = slug(f"{item['artist']} {item['title']}")
                if not wid or wid in seen: continue
                r = get(item["url"])
                if not r: continue
                try:
                    img = Image.open(io.BytesIO(r.content))
                    if min(img.size) < 800: continue
                    wall = make(img, item["kind"])
                except Exception:
                    continue
                wall.save(f"{OUT}/{wid}.webp", "WEBP", quality=80, method=6)
                wall.resize((270, 585), Image.LANCZOS).save(f"{OUT}/thumb/{wid}.webp", "WEBP", quality=75)
                seen.add(wid); n += 1
                found.append(dict(id=wid, title=item["title"][:80], artist=item["artist"][:60], category=category,
                                  credit=item["credit"], source=item["source"], license="Public domain",
                                  image=f"{OUT}/{wid}.webp", thumb=f"{OUT}/thumb/{wid}.webp"))
                print(category, "|", item["artist"], "|", item["title"][:60], flush=True)
    walls = list(old.values()) + found
    # Every third one is free; the rest come with Pro.
    for i, w in enumerate(walls): w["pro"] = i % 3 != 0
    json.dump({"format": "widgetly.wallpapers", "version": 1, "wallpapers": walls}, open("wallpapers.json", "w"), ensure_ascii=False, indent=1)
    print(len(found), "new,", len(walls), "in all")

if __name__ == "__main__":
    main()
