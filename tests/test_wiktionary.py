from vibecheck.wiktionary import select_slang


def entry(word, *senses, pos="adj"):
    return {"word": word, "pos": pos, "lang_code": "en", "senses": list(senses)}


def sense(gloss, *tags):
    return {"glosses": ["parent sense", gloss], "tags": list(tags)}


def test_keeps_slang_informal_and_colloquial_senses():
    records = [
        entry("Boujee", sense("Fancy, upscale.", "US", "slang")),
        entry("comfy", sense("Comfortable.", "informal")),
        entry("lit", sense("Exciting, excellent.", "colloquial"), sense("Lighted.")),
    ]
    df = select_slang(records)
    assert df.to_dict("records") == [
        {"term": "boujee", "pos": "adj", "gloss": "Fancy, upscale."},
        {"term": "comfy", "pos": "adj", "gloss": "Comfortable."},
        {"term": "lit", "pos": "adj", "gloss": "Exciting, excellent."},
    ]


def test_spelling_variants_inherit_slang_senses_of_their_target():
    # "lowkey" is only "Alternative spelling of low-key"; the slang tag sits on "low-key".
    alias = {"glosses": ["Alternative spelling of low-key."], "tags": ["alt-of"], "alt_of": [{"word": "low-key"}]}
    plural = {"glosses": ["plural of slap"], "tags": ["form-of"], "form_of": [{"word": "slap"}]}
    records = [
        entry("lowkey", alias, pos="adv"),
        entry("slaps", plural, pos="verb"),
        entry("low-key", sense("Kind of.", "colloquial"), pos="adv"),
        entry("slap", sense("To be excellent.", "slang"), pos="verb"),
    ]
    df = select_slang(records)
    assert dict(zip(df["term"], df["gloss"], strict=True)) == {
        "low-key": "Kind of.",
        "slap": "To be excellent.",
        "lowkey": "Kind of.",
        "slaps": "To be excellent.",
    }


def test_keeps_derogatory_slang_but_not_offensive():
    records = [entry("bougie", sense("Snobbish, middle-class.", "slang", "derogatory"))]
    assert select_slang(records)["term"].tolist() == ["bougie"]


def test_drops_offensive_senses_names_and_other_languages():
    records = [
        entry("jerkface", sense("A rude person.", "slang", "offensive")),
        entry("Bob", sense("A man's name.", "slang"), pos="name"),
        {**entry("bof", sense("Meh.", "slang")), "lang_code": "fr"},
        entry("wordless"),  # no senses
    ]
    assert select_slang(records).empty
