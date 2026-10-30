"""Filter Google Local California down to SF cafes, restaurants and bars.

    uv run python -m vibecheck.filter_sf            # places, then reviews
    uv run python -m vibecheck.filter_sf places     # places only (fast)

Metadata is downloaded to data/raw. Reviews (5.35 GB) are streamed from the URL.
"""

import gzip
import heapq
import http.client
import re
import shutil
import sys
import urllib.error
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

# Whole-word match on Google categories. The first matching group wins.
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
# Skip categories like "Restaurant supply store".
EXCLUDE_KEYWORDS = ["supply", "supplier", "wholesaler", "equipment", "repair", "manufacturer", "distributor"]


def _word_pattern(words: list[str]) -> re.Pattern:
    """Compile a case-insensitive regex that matches any of `words` as whole words."""
    return re.compile(r"\b(?:" + "|".join(map(re.escape, words)) + r")\b", re.IGNORECASE)


GROUP_PATTERNS = {group: _word_pattern(words) for group, words in CATEGORY_KEYWORDS.items()}
EXCLUDE_PATTERN = _word_pattern(EXCLUDE_KEYWORDS)
OTHER_CITY_PATTERN = re.compile(r", [^,]+, CA \d{5}")  # "..., Daly City, CA 94014"
SF_ADDRESS_PATTERN = re.compile(r"(?:^|, )San Francisco, CA")  # not "South San Francisco, CA"


# --- I/O ---


def download(url: str, path: Path, retries: int = 10) -> Path:
    """Download `url` to `path` with a progress bar. Skips the download if the file exists.

    Resumes from the partial file when the connection stalls or drops (kaikki.org does this).
    """
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".part")
    for attempt in range(retries + 1):
        done = partial.stat().st_size if partial.exists() else 0
        request = urllib.request.Request(url, headers={"Range": f"bytes={done}-"} if done else {})
        try:
            with urllib.request.urlopen(request, timeout=60) as resp:
                if resp.status != 206:  # server sent the whole file, so start over
                    done = 0
                total = done + int(resp.headers["Content-Length"])
                with (
                    tqdm.wrapattr(
                        resp, "read", total=total, initial=done, desc=path.name, unit="B", unit_scale=True
                    ) as src,
                    open(partial, "ab" if done else "wb") as dst,
                ):
                    shutil.copyfileobj(src, dst)
            if partial.stat().st_size >= total:
                break
            error = "connection closed early"  # read() doesn't raise for this, so check the size
        except urllib.error.HTTPError as err:
            if err.code == 416:  # nothing left to fetch: the partial file is complete
                break
            raise
        except (OSError, http.client.IncompleteRead) as err:  # timeouts and dropped connections
            error = err
        if attempt == retries:
            raise ConnectionError(f"{path.name}: gave up after {retries} retries ({error})")
        print(f"{path.name}: {error}. Resuming ({attempt + 1}/{retries})...")
    partial.rename(path)  # only a finished download gets the real name
    return path


def iter_json_lines(source: str | Path) -> Iterator[dict]:
    """Yield records from a gzipped JSON-lines file (path or URL), one line at a time."""
    # If the connection drops, the stream starts over. Download the file if that keeps happening.
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
    """Inside the SF box, and the address says SF or no other city (drops Daly City).

    Address alone isn't enough: it matches South San Francisco and SFO.
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
                # JSON string, since keys differ per place
                "MISC": orjson.dumps(place["MISC"]).decode() if place.get("MISC") else None,
            }
        )
    print(f"{n_total:,} California businesses -> {n_sf:,} in SF -> {len(rows):,} cafes/restaurants/bars")
    return pd.DataFrame(rows)


# --- Reviews ---


def clean_text(text: str | None) -> str | None:
    """Strip text and keep the English part of "(Translated by Google) ... (Original) ..." reviews."""
    if not text:
        return None
    if text.startswith("(Translated by Google)"):
        text = text.removeprefix("(Translated by Google)").split("(Original)")[0]
    return text.strip() or None


def select_reviews(records: Iterable[dict], gmap_ids: set[str], k: int = MAX_REVIEWS_PER_PLACE) -> pd.DataFrame:
    """Keep the `k` most recent non-empty reviews for each place in `gmap_ids`."""
    heaps: dict[str, list] = {}  # gmap_id -> min-heap, oldest review on top
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
    """Read sf_places.parquet with MISC parsed into a `misc` dict. Merges tag spellings like Cosy/Cozy."""
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
    if step == "all" and REVIEWS_OUT.exists():  # the reviews step takes 30-45 min; don't redo it by accident
        print(f"{REVIEWS_OUT.relative_to(ROOT)} already exists. Delete it, or run a single step, to rebuild.")
        sys.exit()
    if step in ("places", "all"):
        build_places()
    if step in ("reviews", "all"):
        build_reviews()
