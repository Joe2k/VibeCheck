"""Slang senses from English Wiktionary (kaikki.org extract), for looking up slang in queries.

    uv run python -m vibecheck.wiktionary

Downloads the 534 MB file to data/raw (resuming when the server stalls) and saves
data/processed/wiktionary_slang.parquet. Skips both if they already exist.
"""

from collections.abc import Iterable

import pandas as pd

from vibecheck.filter_sf import PROCESSED_DIR, RAW_DIR, ROOT, download, iter_json_lines

WIKTIONARY_URL = "https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz"
WIKTIONARY_PATH = RAW_DIR / "kaikki-English.jsonl.gz"
WIKTIONARY_OUT = PROCESSED_DIR / "wiktionary_slang.parquet"

SLANG_TAGS = {"slang", "informal", "colloquial"}
BLOCK_TAGS = {"offensive", "vulgar", "ethnic", "slur"}  # not "derogatory": that would drop "bougie"


def select_slang(records: Iterable[dict]) -> pd.DataFrame:
    """One row per slang sense: lowercased term, part of speech, definition.

    Spelling variants ("lowkey" -> "low-key", "slaps" -> "slap") get their target's slang senses.
    """
    rows, variants = [], set()
    for entry in records:
        if entry.get("lang_code") != "en" or entry.get("pos") == "name":
            continue
        term = entry["word"].lower()
        for sense in entry.get("senses", []):
            for target in sense.get("alt_of", []) + sense.get("form_of", []):
                variants.add((term, target["word"].lower()))
            tags = set(sense.get("tags", []))
            if tags & SLANG_TAGS and not tags & BLOCK_TAGS and sense.get("glosses"):
                rows.append({"term": term, "pos": entry["pos"], "gloss": sense["glosses"][-1]})
    slang = pd.DataFrame(rows, columns=["term", "pos", "gloss"])
    links = pd.DataFrame(sorted(variants), columns=["variant", "term"])
    inherited = links.merge(slang, on="term").drop(columns="term").rename(columns={"variant": "term"})
    return pd.concat([slang, inherited], ignore_index=True).drop_duplicates(ignore_index=True)


def build_wiktionary_slang() -> pd.DataFrame:
    """Read Wiktionary line by line, keep slang senses, and save wiktionary_slang.parquet."""
    source = WIKTIONARY_PATH if WIKTIONARY_PATH.exists() else WIKTIONARY_URL
    slang = select_slang(iter_json_lines(source))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    slang.to_parquet(WIKTIONARY_OUT, index=False)
    n_terms = slang["term"].nunique()
    print(f"Saved {len(slang):,} slang senses for {n_terms:,} terms to {WIKTIONARY_OUT.relative_to(ROOT)}")
    return slang


if __name__ == "__main__":
    if WIKTIONARY_OUT.exists():
        print(f"{WIKTIONARY_OUT.relative_to(ROOT)} already exists")
    else:
        download(WIKTIONARY_URL, WIKTIONARY_PATH)
        build_wiktionary_slang()
