"""Filter the Google Local California dump down to San Francisco cafes, restaurants and bars.

Usage:
    uv run python -m vibecheck.filter_sf            # places, then reviews
    uv run python -m vibecheck.filter_sf places     # places only (fast; use when tuning keywords)

The metadata file (118 MB) is downloaded to data/raw. The reviews file (5.35 GB) is
streamed straight from the URL and never stored, unless you put a copy in data/raw yourself.
"""

import gzip
import heapq
import re
import shutil
import sys
import urllib.request
from collections.abc import Iterable, Iterator
from pathlib import Path

import orjson
import pandas as pd
from tqdm import tqdm

BASE_URL = "https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal"
META_URL = f"{BASE_URL}/meta-California.json.gz"
REVIEWS_URL = f"{BASE_URL}/review-California.json.gz"

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
META_PATH = RAW_DIR / "meta-California.json.gz"
REVIEWS_PATH = RAW_DIR / "review-California.json.gz"  # optional local copy
PLACES_OUT = PROCESSED_DIR / "sf_places.parquet"
REVIEWS_OUT = PROCESSED_DIR / "sf_reviews.parquet"

SF_LAT = (37.70, 37.83)
SF_LON = (-122.52, -122.35)
MAX_REVIEWS_PER_PLACE = 50
ATMOSPHERE_ALIASES = {"Cosy": "Cozy", "Upmarket": "Upscale"}

# --- Tune these. Matched as whole words against each lowercased Google category. ---
# A place's group comes from its first matching category, checked in this order.
CATEGORY_KEYWORDS = {
    "cafe": ["cafe", "café", "coffee", "espresso", "tea house", "bubble tea", "bakery"],
    "restaurant": ["restaurant", "bistro", "diner", "eatery", "steakhouse", "steak house"],
    "bar": [
        "bar",
        "pub",
        "lounge",
        "tavern",
        "brewpub",
        "gastropub",
        "brewery",
        "taproom",
        "night club",
        "beer garden",
        "beer hall",
    ],
}
# Categories containing these words are ignored ("Restaurant supply store", "Coffee machine supplier").
EXCLUDE_KEYWORDS = ["supply", "supplier", "wholesaler", "equipment", "repair", "manufacturer", "distributor"]


def _word_pattern(words: list[str]) -> re.Pattern:
    """Compile a case-insensitive regex that matches any of `words` as whole words."""
    return re.compile(r"\b(?:" + "|".join(map(re.escape, words)) + r")\b", re.IGNORECASE)


GROUP_PATTERNS = {group: _word_pattern(words) for group, words in CATEGORY_KEYWORDS.items()}
EXCLUDE_PATTERN = _word_pattern(EXCLUDE_KEYWORDS)
OTHER_CITY_PATTERN = re.compile(r", [^,]+, CA \d{5}")  # "..., Daly City, CA 94014"
SF_ADDRESS_PATTERN = re.compile(r"(?:^|, )San Francisco, CA")  # not "South San Francisco, CA"


# --- I/O ---


def download(url: str, path: Path) -> Path:
    """Download `url` to `path` with a progress bar. Skips the download if the file exists."""
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    with urllib.request.urlopen(url, timeout=60) as resp:
        total = int(resp.headers["Content-Length"])
        with (
            tqdm.wrapattr(resp, "read", total=total, desc=path.name, unit="B", unit_scale=True) as src,
            open(partial, "wb") as dst,
        ):
            shutil.copyfileobj(src, dst)
    partial.rename(path)  # only a finished download gets the real name
    return path


def iter_json_lines(source: str | Path) -> Iterator[dict]:
    """Stream records from a gzipped JSON-lines file, given a local path or an http(s) URL.

    Reads one line at a time, so memory stays flat no matter how big the file is.
    The progress bar counts compressed bytes read.
    """
    # ponytail: a dropped connection restarts the stream from zero; download the file if that bites.
    if str(source).startswith("http"):
        raw = urllib.request.urlopen(str(source), timeout=60)
        total = int(raw.headers["Content-Length"])
    else:
        raw = open(source, "rb")  # noqa: SIM115 -- closed by the `with` below
        total = Path(source).stat().st_size
    name = str(source).rsplit("/", 1)[-1]
    with (
        raw,
        tqdm.wrapattr(raw, "read", total=total, desc=name, unit="B", unit_scale=True) as tracked,
        gzip.open(tracked) as lines,
    ):
        for line in lines:
            yield orjson.loads(line)


# --- Places ---


def is_in_sf(place: dict) -> bool:
    """True if the place is inside the SF box and its address says SF or names no other city.

    The box is the main rule: an address match alone lets in "South San Francisco, CA" and SFO
    airport ("San Francisco, CA 94128"), both south of the city. The address check stops the box
    from pulling in the edge of Daly City, while keeping SF addresses written in other formats.
    Places without coordinates fall back to the address.
    """
    address = place.get("address") or ""
    says_sf = SF_ADDRESS_PATTERN.search(address) is not None
    lat, lon = place.get("latitude"), place.get("longitude")
    if lat is None or lon is None:
        return says_sf
    in_box = SF_LAT[0] <= lat <= SF_LAT[1] and SF_LON[0] <= lon <= SF_LON[1]
    return in_box and (says_sf or not OTHER_CITY_PATTERN.search(address))


def category_group(categories: list[str] | None) -> str | None:
    """Return "cafe", "restaurant" or "bar" for the first matching category, or None."""
    for category in categories or []:
        if EXCLUDE_PATTERN.search(category):
            continue
        for group, pattern in GROUP_PATTERNS.items():
            if pattern.search(category):
                return group
    return None


def select_places(records: Iterable[dict]) -> pd.DataFrame:
    """Keep SF cafes, restaurants and bars; one row per unique gmap_id."""
    rows, seen, n_total, n_sf = [], set(), 0, 0
    for place in records:
        n_total += 1
        if not is_in_sf(place):
            continue
        n_sf += 1
        group = category_group(place.get("category"))
        if group is None or place["gmap_id"] in seen:
            continue
        seen.add(place["gmap_id"])
        rows.append(
            {
                "gmap_id": place["gmap_id"],
                "name": place.get("name"),
                "address": place.get("address"),
                "lat": place.get("latitude"),
                "lon": place.get("longitude"),
                "group": group,
                "category": place.get("category"),
                "avg_rating": place.get("avg_rating"),
                "num_of_reviews": place.get("num_of_reviews"),
                "price": place.get("price"),
                # Stored as a JSON string: its keys differ from place to place.
                "MISC": orjson.dumps(place["MISC"]).decode() if place.get("MISC") else None,
            }
        )
    print(f"{n_total:,} California businesses -> {n_sf:,} in SF -> {len(rows):,} cafes/restaurants/bars")
    return pd.DataFrame(rows)


# --- Reviews ---


def clean_text(text: str | None) -> str | None:
    """Strip whitespace and keep only the English part of Google-translated reviews.

    Translated reviews look like "(Translated by Google) <english>\\n\\n(Original)\\n<original>".
    Returns None for empty text.
    """
    if not text:
        return None
    if text.startswith("(Translated by Google)"):
        text = text.removeprefix("(Translated by Google)").split("(Original)")[0]
    return text.strip() or None


def select_reviews(records: Iterable[dict], gmap_ids: set[str], k: int = MAX_REVIEWS_PER_PLACE) -> pd.DataFrame:
    """Keep the `k` most recent non-empty reviews for each place in `gmap_ids`."""
    heaps: dict[str, list] = {}  # gmap_id -> min-heap of (time, counter, review), oldest on top
    for counter, review in enumerate(records):
        if review["gmap_id"] not in gmap_ids:
            continue
        text = clean_text(review.get("text"))
        if text is None:
            continue
        item = (review["time"], counter, {**review, "text": text})
        heap = heaps.setdefault(review["gmap_id"], [])
        if len(heap) < k:
            heapq.heappush(heap, item)
        elif item > heap[0]:
            heapq.heapreplace(heap, item)

    rows = [
        {key: review[key] for key in ("gmap_id", "user_id", "time", "rating", "text")}
        for heap in heaps.values()
        for _, _, review in heap
    ]
    df = pd.DataFrame(rows, columns=["gmap_id", "user_id", "time", "rating", "text"])
    df = df.drop_duplicates(["gmap_id", "user_id", "time"]).drop(columns="user_id")
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    return df.sort_values(["gmap_id", "time"], ascending=[True, False], ignore_index=True)


# --- Pipeline ---


def load_places() -> pd.DataFrame:
    """Read sf_places.parquet and parse MISC into a dict column `misc` ({} when missing).

    Google spells some Atmosphere tags two ways; those are merged so "Cosy" places count as "Cozy".
    """
    places = pd.read_parquet(PLACES_OUT)
    places["misc"] = [orjson.loads(s) if isinstance(s, str) else {} for s in places["MISC"]]
    for misc in places["misc"]:
        if "Atmosphere" in misc:
            merged = (ATMOSPHERE_ALIASES.get(tag, tag) for tag in misc["Atmosphere"])
            misc["Atmosphere"] = list(dict.fromkeys(merged))  # dedupe, keep order
    return places


def build_places() -> pd.DataFrame:
    """Download the metadata (once), filter it, and save sf_places.parquet."""
    places = select_places(iter_json_lines(download(META_URL, META_PATH)))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    places.to_parquet(PLACES_OUT, index=False)
    print(f"Saved {PLACES_OUT.relative_to(ROOT)}")
    return places


def build_reviews() -> pd.DataFrame:
    """Stream the reviews file, keep reviews for SF places, and save sf_reviews.parquet."""
    gmap_ids = set(pd.read_parquet(PLACES_OUT, columns=["gmap_id"])["gmap_id"])
    source = REVIEWS_PATH if REVIEWS_PATH.exists() else REVIEWS_URL
    reviews = select_reviews(iter_json_lines(source), gmap_ids)
    reviews.to_parquet(REVIEWS_OUT, index=False)
    n_places = reviews["gmap_id"].nunique()
    print(f"Saved {len(reviews):,} reviews for {n_places:,} places to {REVIEWS_OUT.relative_to(ROOT)}")
    return reviews


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step in ("places", "all"):
        build_places()
    if step in ("reviews", "all"):
        build_reviews()
