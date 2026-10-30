"""Test queries labeled by Google's tags, and a throwaway keyword scorer to show the slang gap.

Each tag gets a plain and a slang query with the same meaning. The relevant places are the ones
Google tags that way. These are silver labels: tags are noisy, but free.
"""

import re
from collections import Counter

import pandas as pd
from spacy.lang.en.stop_words import STOP_WORDS

# Add more queries here. group limits results to one place type (None = all).
TAG_QUERIES = [
    {"misc_key": "Atmosphere", "tag": "Cozy", "group": "cafe",
     "plain": "cozy cafe with comfortable seating", "slang": "comfy lowkey cafe to chill"},
    {"misc_key": "Atmosphere", "tag": "Romantic", "group": "restaurant",
     "plain": "romantic restaurant for a date night", "slang": "restaurant to impress bae"},
    {"misc_key": "Atmosphere", "tag": "Upscale", "group": "restaurant",
     "plain": "upscale fancy elegant restaurant", "slang": "boujee restaurant to flex"},
    {"misc_key": "Atmosphere", "tag": "Historic", "group": None,
     "plain": "historic old place with a long history", "slang": "og old school spot"},
    {"misc_key": "Atmosphere", "tag": "Trending", "group": None,
     "plain": "trendy popular new bar", "slang": "poppin bar everyone is hyped about"},
    {"misc_key": "Popular for", "tag": "Good for working on laptop", "group": "cafe",
     "plain": "quiet cafe to work on my laptop with wifi", "slang": "cafe to grind on homework"},
    {"misc_key": "Crowd", "tag": "College students", "group": None,
     "plain": "cheap place popular with college students", "slang": "spot for broke college kids"},
    {"misc_key": "Crowd", "tag": "Groups", "group": "restaurant",
     "plain": "restaurant good for large groups of friends", "slang": "restaurant for the whole squad"},
]  # fmt: skip


def relevant_places(places: pd.DataFrame, misc_key: str, tag: str, group: str | None = None) -> set[str]:
    """gmap_ids that Google tags with `tag` (optionally only cafes, restaurants or bars)."""
    tagged = places["misc"].map(lambda misc: tag in misc.get(misc_key, []))
    if group:
        tagged &= places["group"] == group
    return set(places.loc[tagged, "gmap_id"])


def content_words(text: str) -> list[str]:
    """Lowercased words, without stopwords."""
    return [w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOP_WORDS]


def keyword_rank(query: str, place_text: pd.Series, k: int = 10) -> list[str]:
    """Top `k` places by how many query words their reviews use (ties: total mentions). Not BM25."""
    words = set(content_words(query))
    scored = []
    for gmap_id, text in place_text.items():
        counts = Counter(content_words(text))
        distinct = sum(counts[w] > 0 for w in words)
        if distinct:
            scored.append((-distinct, -sum(counts[w] for w in words), gmap_id))
    return [gmap_id for _, _, gmap_id in sorted(scored)[:k]]


def precision_at_k(ranked: list[str], relevant: set[str], k: int = 10) -> float:
    """Share of the top `k` slots filled by relevant places."""
    return sum(gmap_id in relevant for gmap_id in ranked[:k]) / k


def run_queries(places: pd.DataFrame, reviews: pd.DataFrame, queries: list[dict] = TAG_QUERIES, k: int = 10):
    """P@k of the keyword scorer for the plain and slang version of each query."""
    place_text = reviews.groupby("gmap_id")["text"].agg(" ".join)
    rows = []
    for q in queries:
        relevant = relevant_places(places, q["misc_key"], q["tag"], q["group"])
        pool = place_text
        if q["group"]:
            pool = place_text[place_text.index.isin(places.loc[places["group"] == q["group"], "gmap_id"])]
        rows.append(
            {
                "tag": q["tag"],
                "relevant places": len(relevant),
                "chance": len(relevant & set(pool.index)) / len(pool),  # P@k of picking at random
                "plain query": q["plain"],
                f"P@{k} plain": precision_at_k(keyword_rank(q["plain"], pool, k), relevant, k),
                "slang query": q["slang"],
                f"P@{k} slang": precision_at_k(keyword_rank(q["slang"], pool, k), relevant, k),
            }
        )
    return pd.DataFrame(rows)
