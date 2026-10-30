import pandas as pd

from vibecheck.evaluate import keyword_rank, precision_at_k, relevant_places, run_queries

PLACES = pd.DataFrame(
    {
        "gmap_id": ["a", "b", "c"],
        "group": ["cafe", "cafe", "bar"],
        "misc": [{"Atmosphere": ["Cozy"]}, {}, {"Atmosphere": ["Cozy"]}],
    }
)
PLACE_TEXT = pd.Series({"a": "so cozy and warm", "b": "cozy cozy cozy", "c": "cozy bar, warm vibe"})


def test_relevant_places_uses_tag_and_group():
    assert relevant_places(PLACES, "Atmosphere", "Cozy") == {"a", "c"}
    assert relevant_places(PLACES, "Atmosphere", "Cozy", group="cafe") == {"a"}


def test_keyword_rank_prefers_more_distinct_query_words():
    # "a" and "c" match both "cozy" and "warm"; "b" only "cozy". Stopwords ("a", "to") are ignored.
    assert keyword_rank("a cozy warm place to sit", PLACE_TEXT, k=2) == ["a", "c"]


def test_keyword_rank_drops_places_with_no_match():
    assert keyword_rank("boujee", PLACE_TEXT, k=10) == []


def test_precision_at_k_divides_by_k():
    assert precision_at_k(["a", "b"], {"a"}, k=10) == 0.1


def test_run_queries_scores_plain_and_slang():
    queries = [{"misc_key": "Atmosphere", "tag": "Cozy", "group": "cafe", "plain": "cozy cafe", "slang": "boujee"}]
    reviews = pd.DataFrame({"gmap_id": ["a", "b"], "text": ["cozy little cafe", "cozy cozy"]})
    row = run_queries(PLACES, reviews, queries, k=1).iloc[0]
    assert (row["relevant places"], row["P@1 plain"], row["P@1 slang"]) == (1, 1.0, 0.0)
    assert row["chance"] == 0.5  # 1 relevant cafe out of 2 cafes with reviews
