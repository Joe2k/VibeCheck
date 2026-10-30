import pandas as pd

from vibecheck.lexicon import best_definitions, gap_table, term_pattern


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


def test_best_definitions_picks_top_voted_and_marks_missing():
    defs = pd.DataFrame(
        {
            "word": ["Lowkey", "lowkey"],
            "up_votes": [300, 900],
            "definition": ["quietly", "to keep;;things secret"],
        }
    )
    best = best_definitions(defs, ["lowkey", "boujee"])
    assert best["lowkey"] == "to keep things secret"
    assert pd.isna(best["boujee"])
