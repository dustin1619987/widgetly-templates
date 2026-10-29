# Photo wallpapers for the photo themes (cities, nature, plants, everyday
# life, animals): public-domain and CC0 photos from Wikimedia Commons, its
# rated Quality images first.
#
# For each theme in THEMES that isn't picked yet, saves up to 12 candidates
# (cropped to a phone, as small previews) in candidates/<key>/ with their
# details in candidates/<key>.json, to look through. Pictures of people are
# skipped: by their tags, title and a face check.
# For each theme picked in scripts/theme_picks.json ({"key": candidate
# number, or {"n": number, "x": 0.3} to crop left of center}), downloads that photo full size into themes/photo_<key>.webp.
import json, os, re, sys, time, io
import requests
from PIL import Image, ImageOps
import cv2, numpy as np

W, H = 1080, 2340
API = "https://api.openverse.org/v1/images/"
UA = {"User-Agent": "Widgetly wallpapers (github.com/dustin1619987/widgetly-templates)"}

THEMES = {
    # Cities
    "new_york": "new york skyline night", "paris": "eiffel tower paris", "tokyo": "tokyo night street",
    "london": "london tower bridge", "venice": "venice canal", "santorini": "santorini oia",
    "golden_gate": "golden gate bridge", "chicago": "chicago skyline", "hong_kong": "hong kong skyline night",
    "rome": "rome colosseum", "amsterdam": "amsterdam canal houses", "seoul": "seoul night city",
    "kyoto": "kyoto temple autumn", "city_rain": "city street rain night", "city_sunset": "city skyline sunset",
    "old_town": "cobblestone street old town", "las_vegas": "las vegas strip night", "miami": "miami beach skyline",
    # Nature
    "mountain_lake": "mountain lake reflection", "yosemite": "yosemite valley", "waterfall": "waterfall forest",
    "desert_dunes": "sand dunes desert", "misty_forest": "foggy forest trees", "lavender": "lavender field",
    "autumn_leaves": "autumn forest path", "snowy_peaks": "snowy mountains", "tropical_beach": "tropical beach palm trees",
    "ocean_waves": "ocean wave", "aurora": "aurora borealis", "canyon": "grand canyon",
    "milky_way": "milky way night sky", "green_hills": "green hills countryside", "sunflower_field": "sunflower field",
    "tulip_field": "tulip field", "cherry_blossom": "cherry blossom tree", "lake_sunrise": "lake sunrise dock",
    "rainforest": "rainforest jungle", "lightning": "lightning storm", "clouds": "clouds sky pink sunset",
    # Plants
    "monstera": "monstera leaf", "succulents": "succulent plants", "cactus": "cactus desert",
    "ferns": "fern leaves", "houseplants": "houseplants indoor", "moss": "moss forest floor",
    "palm_leaves": "palm leaves", "roses": "red roses", "wildflowers": "wildflower meadow",
    "lotus": "lotus flower pond", "daisies": "daisy flowers", "hydrangea": "hydrangea",
    "orchid": "orchid flower", "bamboo": "bamboo forest",
    # Everyday life
    "coffee": "coffee cup latte", "books": "library books shelves", "vinyl": "vinyl record player",
    "candles": "candles light", "rainy_window": "rain drops window", "bakery": "bread bakery",
    "vintage_car": "vintage car", "train": "railway train tracks", "bicycle": "bicycle flowers",
    "balloons": "hot air balloons", "lanterns": "paper lanterns", "fairy_lights": "string lights bokeh",
    "fruit": "fresh fruit market", "pizza": "pizza", "sushi": "sushi", "donuts": "donuts",
    # Animals
    "cat_nap": "cat sleeping", "puppy": "puppy dog", "fox": "red fox", "horses": "horses field",
    "butterflies": "butterfly flower", "songbird": "bird on branch", "jellyfish": "jellyfish",
    "sea_turtle": "sea turtle", "deer": "deer forest", "owl": "owl", "penguins": "penguins",
    "bunny": "rabbit grass", "elephant": "elephant", "koi": "koi fish pond",
    # Batch 2: weekly drops (retries of ones that had no good photo, then new ideas)
    "amsterdam2": "amsterdam canal night", "seoul2": "gyeongbokgung palace", "miami2": "miami beach palm trees",
    "prague": "prague charles bridge", "ocean2": "ocean wave crashing rocks", "rainforest2": "rainforest waterfall jungle",
    "lightning2": "lightning bolt night sky", "rain_glass": "raindrops on glass", "croissants": "croissants",
    "bookshelf": "bookshelf books", "vinyl2": "vinyl records", "classic_car": "classic car", "pizza2": "pizza margherita",
    "steam_train": "steam train", "wild_rabbit": "wild rabbit", "deer2": "deer meadow", "african_elephant": "african elephant",
    "wild_horses": "wild horses", "koi2": "koi fish", "emperor_penguins": "emperor penguins", "sea_turtle2": "sea turtle underwater",
    "dubai": "dubai skyline night", "sydney": "sydney opera house", "singapore": "marina bay sands night",
    "istanbul": "istanbul mosque sunset", "barcelona": "sagrada familia", "hallstatt": "hallstatt", "cinque_terre": "cinque terre",
    "shanghai": "shanghai skyline night", "rio": "rio de janeiro sugarloaf", "neon_signs": "neon sign night", "bangkok": "bangkok temple",
    "machu_picchu": "machu picchu", "taj_mahal": "taj mahal", "iceland_falls": "iceland waterfall", "fjord": "norway fjord",
    "rice_terraces": "rice terraces", "bluebells": "bluebell woods", "lagoon": "tropical lagoon maldives", "volcano": "volcano lava",
    "glacier": "glacier ice", "rainbow": "rainbow landscape", "mountain_sunrise": "mountain sunrise", "sea_cliffs": "sea cliffs coast",
    "frozen_lake": "frozen lake winter", "wheat": "golden wheat field", "poppies": "poppy field", "peonies": "peony flowers",
    "magnolia": "magnolia blossom", "wisteria": "wisteria", "lilac": "lilac flowers", "maple": "red maple leaves",
    "pumpkins": "pumpkins autumn", "christmas_lights": "christmas lights", "snowy_pines": "snowy pine forest",
    "hot_chocolate": "hot chocolate mug", "fireplace": "fireplace fire", "ice_cream": "ice cream cone", "macarons": "macarons",
    "tea_time": "tea cup teapot", "campfire": "campfire night", "ferris_wheel": "ferris wheel night", "carousel": "carousel lights",
    "sailboat": "sailboat sunset", "lighthouse": "lighthouse", "hummingbird": "hummingbird", "dolphins": "dolphins",
    "panda": "giant panda", "kitten": "kitten", "golden_retriever": "golden retriever", "swans": "swans lake",
    "flamingo": "flamingo", "peacock": "peacock feathers", "tiger": "tiger", "lion": "lion", "whale": "humpback whale",
    "hedgehog": "hedgehog", "red_panda": "red panda", "ladybug": "ladybug", "bee": "bee flower",
}

PEOPLE_TAGS = {"person", "people", "man", "woman", "men", "women", "girl", "boy", "child", "children", "kid",
               "portrait", "face", "selfie", "crowd", "adult", "model", "family", "couple", "tourist", "tourists"}
AVOID = re.compile(r"portrait|wom[ae]n|\bm[ae]n\b|girl|boy|child|kid|people|person|selfie|model|wedding|bride|crowd|family|nude|dead|hunt", re.I)
faces = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")


def crop(img, x=0.5):
    img = ImageOps.exif_transpose(img).convert("RGB")
    return ImageOps.fit(img, (W, H), Image.LANCZOS, centering=(x, 0.5))


def has_face(img):
    gray = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)
    scale = 1200 / max(gray.shape)
    if scale < 1: gray = cv2.resize(gray, None, fx=scale, fy=scale)
    found = faces.detectMultiScale(gray, 1.1, 8, minSize=(30, 30))
    return any(w * h > gray.size * 0.004 for _, _, w, h in found)


COMMONS = "https://commons.wikimedia.org/w/api.php"
FREE = "haswbstatement:P275=Q6938433|P6216=Q19652"  # CC0, or public domain


def search(query, page):
    """Commons photos for [query] that are CC0 or public domain and don't depict people: rated Quality images first."""
    found = []
    for extra in ("incategory:Quality_images", ""):
        params = dict(action="query", format="json", generator="search", gsrnamespace=6, gsrlimit=50,
                      gsrsearch=f"{query} filetype:bitmap {FREE} -haswbstatement:P180=Q5 {extra}".strip(),
                      prop="imageinfo", iiprop="url|size|extmetadata|mime", iiurlheight=2400)
        for wait in (5, 20, 60):
            r = requests.get(COMMONS, params=params, headers=UA, timeout=60)
            if r.status_code == 429: time.sleep(wait); continue
            r.raise_for_status()
            pages = sorted(r.json().get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
            for p in pages:
                info = (p.get("imageinfo") or [{}])[0]
                meta = info.get("extmetadata", {})
                lic = meta.get("LicenseShortName", {}).get("value", "")
                if not re.search(r"cc0|public domain|pd", lic, re.I): continue
                if info.get("mime") not in ("image/jpeg", "image/png", "image/webp"): continue
                artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()
                found.append(dict(url=info.get("thumburl") or info["url"], orig=info["url"], width=info.get("width"), height=info.get("height"),
                                  title=p["title"].removeprefix("File:").rsplit(".", 1)[0], creator=artist,
                                  license="cc0" if "cc0" in lic.lower() else "pdm", foreign_landing_url=info.get("descriptionurl"),
                                  source="Wikimedia Commons", tags=[], quality=bool(extra)))
            break
        time.sleep(1)
    seen, out = set(), []
    for f in found:
        if f["url"] not in seen: seen.add(f["url"]); out.append(f)
    return out if page == 1 else []


def fetch(url):
    for wait in (15, 45, 90, 180):
        r = requests.get(url, headers=UA, timeout=60)
        if r.status_code != 429: break
        time.sleep(wait)
    r.raise_for_status()
    if len(r.content) > 40_000_000: raise ValueError("too big")
    return Image.open(io.BytesIO(r.content))


def candidates(key, query):
    out, seen = [], set()
    for page in (1, 2):
        for item in search(query, page):
            if len(out) >= 12: break
            w, h = item.get("width") or 0, item.get("height") or 0
            if item.get("mature") or item["url"] in seen: continue
            if w and h and (h < 1500 and w < 2400): continue
            tags = {t["name"].lower() for t in item.get("tags") or []}
            if tags & PEOPLE_TAGS or AVOID.search(item.get("title") or ""): continue
            seen.add(item["url"])
            try:
                try:
                    img = fetch(item["url"])
                except Exception:
                    if not item.get("orig"): raise
                    item["url"] = item["orig"]; img = fetch(item["url"])
                if img.size[1] < 1400: continue
                if has_face(img): continue
                small = crop(img).resize((240, 520), Image.LANCZOS)
            except Exception as e:
                print("  skip", item["url"], e); continue
            os.makedirs(f"candidates/{key}", exist_ok=True)
            small.save(f"candidates/{key}/{len(out)}.jpg", quality=80)
            out.append(dict(url=item["url"], title=item.get("title") or "", creator=item.get("creator") or "",
                            license=item.get("license", ""), source=item.get("foreign_landing_url") or "",
                            provider=item.get("source") or item.get("provider") or "", quality=item.get("quality", False)))
        time.sleep(2)
    json.dump(out, open(f"candidates/{key}.json", "w"), indent=1, ensure_ascii=False)
    print(key, len(out))


def main():
    picks = json.load(open("scripts/theme_picks.json")) if os.path.exists("scripts/theme_picks.json") else {}
    os.makedirs("candidates", exist_ok=True)
    for key, query in THEMES.items():
        if key in picks:
            path = f"themes/photo_{key}.webp"
            if os.path.exists(path): continue
            pick = picks[key] if isinstance(picks[key], dict) else {"n": picks[key]}
            item = json.load(open(f"candidates/{key}.json"))[pick["n"]]
            crop(fetch(item["url"]), pick.get("x", 0.5)).save(path, "WEBP", quality=82, method=6)
            print("picked", key, item["url"])
            time.sleep(3)
        elif not os.path.exists(f"candidates/{key}.json") or not json.load(open(f"candidates/{key}.json")):
            try: candidates(key, query)
            except Exception as e: print("failed", key, e)


if __name__ == "__main__":
    main()
