from vibecheck.filter_sf import category_group, clean_text, is_in_sf, select_places, select_reviews


def test_category_group():
    assert category_group(["Coffee shop", "Bakery"]) == "cafe"
    assert category_group(["Cocktail bar"]) == "bar"
    assert category_group(["Barber shop"]) is None  # "bar" must be a whole word
    assert category_group(["Restaurant supply store"]) is None
    assert category_group(None) is None


def test_is_in_sf():
    assert is_in_sf({"address": "Blue Bottle, 66 Mint St, San Francisco, CA 94103"})
    assert is_in_sf({"address": None, "latitude": 37.77, "longitude": -122.42})
    assert not is_in_sf({"address": "Oakland, CA", "latitude": 37.80, "longitude": -122.27})
    assert not is_in_sf(
        {"address": "X, 6192 Mission St, Daly City, CA 94014", "latitude": 37.705, "longitude": -122.46}
    )


def test_clean_text():
    assert clean_text("(Translated by Google) Great coffee\n\n(Original)\nCafé genial") == "Great coffee"
    assert clean_text("  ") is None
    assert clean_text(None) is None


def test_select_places_dedupes():
    place = {
        "gmap_id": "a",
        "address": "X, San Francisco, CA",
        "category": ["Wine bar"],
        "MISC": {"Atmosphere": ["Cozy"]},
    }
    df = select_places([place, place])
    assert len(df) == 1 and df.loc[0, "group"] == "bar" and df.loc[0, "MISC"] == '{"Atmosphere":["Cozy"]}'


def test_select_reviews_keeps_k_most_recent():
    records = [{"gmap_id": "a", "user_id": str(t), "time": t, "rating": 5, "text": f"r{t}"} for t in range(10)]
    records += [{"gmap_id": "a", "user_id": "x", "time": 99, "rating": 1, "text": None}]  # empty: dropped
    records += [{"gmap_id": "other", "user_id": "y", "time": 50, "rating": 1, "text": "not SF"}]
    df = select_reviews(records, {"a"}, k=3)
    assert df["text"].tolist() == ["r9", "r8", "r7"]
