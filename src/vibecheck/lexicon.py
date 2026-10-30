"""Word lists for the vibe and slang stats, and Urban Dictionary lookups."""

import re
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from vibecheck.filter_sf import RAW_DIR

UD_CSV = RAW_DIR / "urbandict-word-defs.csv"

# Plain words reviewers use for atmosphere.
VIBE_WORDS = [
    "atmosphere", "ambiance", "ambience", "vibe", "vibes", "decor", "cozy", "cosy", "intimate",
    "romantic", "quiet", "loud", "noisy", "lively", "crowded", "packed", "spacious", "cramped",
    "music", "lighting", "dim", "chill", "relaxed", "laid-back", "casual", "trendy", "upscale",
]  # fmt: skip

# query -> (slang forms, plain words with the same meaning).
# Picked before counting, all rows reported. Left out as ambiguous:
# "lit" (dimly lit), "fire" (wood-fired), "grind" (coffee grind), "mid" (mid-week).
GAP_QUERIES = {
    "boujee": (["boujee", "bougie", "bourgie"], ["fancy", "upscale", "classy", "elegant", "luxurious"]),
    "lowkey": (["lowkey"], ["low-key", "low key", "laid-back", "unpretentious", "understated"]),
    "vibey": (["vibey", "vibes"], ["atmosphere", "ambiance", "ambience"]),
    "aesthetic": (["aesthetic"], ["beautiful", "gorgeous", "stylish", "decor"]),  # not "pretty" (pretty good)
    "chill": (["chill"], ["relaxed", "relaxing", "calm", "mellow", "laid-back"]),
    "bussin": (["bussin", "bussin'"], ["delicious", "tasty", "flavorful"]),
    "slaps": (["slaps", "slapped"], ["delicious", "tasty", "flavorful"]),
    "goated": (["goated"], ["the best", "excellent", "outstanding"]),
    "poppin": (["poppin", "poppin'"], ["lively", "bustling", "busy", "packed"]),
    "instagrammable": (["instagrammable", "insta-worthy", "ig-worthy"], ["photogenic", "picturesque"]),
    "sus": (["sus"], ["sketchy", "shady", "suspicious"]),
    "turnt": (["turnt"], ["rowdy", "wild", "rambunctious"]),  # not "party" (party of 6)
}

# Urban Dictionary filters. A term needs at least one well-voted definition.
MIN_UPVOTES = 100
MIN_UPVOTE_RATIO = 0.7


def term_pattern(terms: Iterable[str]) -> re.Pattern:
    """Case-insensitive whole-word regex for any of `terms` (handles "poppin'" and "low-key")."""
    alternatives = "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alternatives})(?!\w)", re.IGNORECASE)


def gap_table(reviews: pd.DataFrame, queries: dict = GAP_QUERIES) -> pd.DataFrame:
    """Reviews and places mentioning each slang word vs. its plain meaning."""
    rows = []
    for query, (slang, plain) in queries.items():
        has_slang = reviews["text"].str.contains(term_pattern(slang))
        has_plain = reviews["text"].str.contains(term_pattern(plain))
        rows.append(
            {
                "query": query,
                "plain meaning": ", ".join(plain),
                "reviews (slang)": int(has_slang.sum()),
                "reviews (plain)": int(has_plain.sum()),
                "places (slang)": reviews.loc[has_slang, "gmap_id"].nunique(),
                "places (plain)": reviews.loc[has_plain, "gmap_id"].nunique(),
            }
        )
    return pd.DataFrame(rows)


def load_ud_definitions(path: Path = UD_CSV, chunksize: int = 200_000) -> pd.DataFrame:
    """Read the Urban Dictionary CSV in chunks, keeping well-voted definitions."""
    keep = []
    for chunk in pd.read_csv(
        path,
        usecols=["word", "up_votes", "down_votes", "definition"],
        chunksize=chunksize,
        on_bad_lines="skip",
        dtype=str,
    ):
        chunk = chunk.dropna()
        up = pd.to_numeric(chunk["up_votes"], errors="coerce").fillna(0)
        down = pd.to_numeric(chunk["down_votes"], errors="coerce").fillna(0)
        ratio = up / (up + down).clip(lower=1)
        keep.append(chunk.assign(up_votes=up, ratio=ratio)[(up >= MIN_UPVOTES) & (ratio >= MIN_UPVOTE_RATIO)])
    return pd.concat(keep, ignore_index=True)[["word", "up_votes", "ratio", "definition"]]


def best_definitions(definitions: pd.DataFrame, terms: Iterable[str]) -> pd.Series:
    """Top-voted Urban Dictionary definition for each term (NaN if UD doesn't have it)."""
    defs = definitions.assign(term=definitions["word"].str.lower().str.strip())
    best = defs.sort_values("up_votes", ascending=False).drop_duplicates("term").set_index("term")
    return best["definition"].str.replace(";;", " ").reindex(list(terms))
