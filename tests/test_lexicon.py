import pandas as pd

from vibecheck.lexicon import build_slang_lexicon, find_terms, gap_table, is_slang_term, term_pattern


def test_term_pattern_whole_words():
    pattern = term_pattern(["sus", "poppin'", "low-key"])
    assert pattern.search("Kinda SUS tbh")
    assert pattern.search("place was poppin' last night")
    assert pattern.search("a low-key spot")
    assert not pattern.search("great sushi")


def test_gap_table_counts_reviews_and_places():
    reviews = pd.DataFrame(
        {
            "gmap_id": ["a", "a", "b"],
            "text": ["so boujee", "fancy and classy", "Fancy decor"],
        }
    )
    row = gap_table(reviews, {"boujee": (["boujee"], ["fancy", "classy"])}).iloc[0]
    assert (row["reviews (slang)"], row["reviews (plain)"]) == (1, 2)
    assert (row["places (slang)"], row["places (plain)"]) == (1, 2)


def test_is_slang_term():
    assert is_slang_term("boujee", up_votes=500)
    assert not is_slang_term("coffee", up_votes=5000)  # common English
    assert not is_slang_term("asdfgh", up_votes=5000)  # wordfreq never saw it
    assert not is_slang_term("low key", up_votes=200)  # phrases need more votes
    assert is_slang_term("low key", up_votes=2000)
    assert not is_slang_term("a b c", up_votes=9999)


def test_build_slang_lexicon_blocks_flagged_terms():
    defs = pd.DataFrame(
        {
            "word": ["Boujee", "boujee", "jaxon"],
            "up_votes": [900, 300, 800],
            "ratio": [0.9, 0.8, 0.9],
            "definition": ["fancy, high-class", "rich", "a name for the best guy"],
        }
    )
    lexicon = build_slang_lexicon(defs)
    assert lexicon["term"].tolist() == ["boujee"]
    assert lexicon.loc[0, "definition"] == "fancy, high-class"  # best-voted definition wins


def test_find_terms_unigrams_and_bigrams():
    assert find_terms("Lowkey the best, low key vibes", {"lowkey", "low key"}) == ["lowkey", "low key"]
