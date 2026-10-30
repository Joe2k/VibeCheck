"""Word lists for the vibe and slang stats, plus the Urban Dictionary slang lexicon."""

import re
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
from wordfreq import zipf_frequency

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
MAX_ZIPF = 3.0  # single words must be rare in everyday English
TERM_RE = re.compile(r"[a-z]+(?:['-][a-z]+)*(?: [a-z]+(?:['-][a-z]+)*)?")  # one or two words
# Crude offensive/junk screens. Add words as junk shows up.
# Definitions: drop the term if any good definition mentions these.
BLOCK_MARKERS = re.compile(
    r"\b(?:sex\w*|penis|vagina|genital\w*|porn\w*|masturbat\w*|slur\w*|racis\w*|racial|ethnic|"
    r"derogatory|insult\w*|offensive|nazi|rape\w*|name|named)\b",
    re.IGNORECASE,
)
# Terms: drop if the term itself contains these.
PROFANITY = re.compile(
    r"fuck|shit|bitch|cunt|dick|cock|puss|anal|anus|nigg|fag|whore|slut|tits|boob|homo|retard|rape|sex|porn|"
    r"penis|vagina|jizz|nazi|ching|chong",
    re.IGNORECASE,
)


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


def is_slang_term(term: str, ud_terms: set[str]) -> bool:
    """Rare single words, or phrases UD also has as one word ("low key" -> "lowkey")."""
    if len(term) < 3 or not TERM_RE.fullmatch(term) or PROFANITY.search(term):
        return False
    if " " in term:
        return term.replace(" ", "") in ud_terms  # Zipf can't judge phrases
    return 0 < zipf_frequency(term, "en") < MAX_ZIPF  # 0 means wordfreq never saw it: likely junk


def build_slang_lexicon(definitions: pd.DataFrame) -> pd.DataFrame:
    """One row per slang term: its best definition, votes and Zipf frequency."""
    defs = definitions.assign(term=definitions["word"].str.lower().str.strip())
    blocked = set(defs.loc[defs["definition"].str.contains(BLOCK_MARKERS), "term"])
    best = defs.sort_values("up_votes", ascending=False).drop_duplicates("term")
    best = best[~best["term"].isin(blocked)]
    ud_terms = set(best["term"])
    best = best[[is_slang_term(t, ud_terms) for t in best["term"]]]
    best = best.assign(zipf=best["term"].map(lambda t: zipf_frequency(t, "en")))
    return best[["term", "up_votes", "ratio", "zipf", "definition"]].reset_index(drop=True)


def find_terms(text: str, lexicon: set[str]) -> list[str]:
    """Lexicon words and two-word phrases found in `text`."""
    words = re.findall(r"[a-z]+(?:['-][a-z]+)*", text.lower())
    bigrams = [f"{a} {b}" for a, b in zip(words, words[1:], strict=False)]
    return [t for t in words + bigrams if t in lexicon]
