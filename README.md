# VibeCheck

Search SF cafes, restaurants and bars the way you talk:
*"a lowkey aesthetic cafe to grind on some work"*. Results come from Google Maps reviews.

CS 667 (NLP) class project. This repo is the data + features stage. Search comes next.

## The problem

Users search with slang. Reviewers mostly don't. In our SF data, 32 places have a review
saying "boujee" and 1,154 say "fancy", "upscale" or "classy". Keyword search misses most of them.
Full numbers: [reports/numbers.md](reports/numbers.md).

## Setup

Needs [uv](https://docs.astral.sh/uv/) and ~4 GB of free disk.

```bash
make setup   # .venv with Python 3.11 + all deps
make test
```

No uv: `python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt -e .`

Kaggle token (for the slang notebook): Kaggle → Settings → API → Create New Token, then

```bash
mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json
```

## Run

```bash
make data       # SF places + reviews, Urban Dictionary, Wiktionary slang (~1 h, mostly streaming)
make stats      # notebooks 00-03, writes reports/numbers.md
make features   # notebook 04 (~1 GB of models on first run)
```

Or `uv run jupyter lab` and step through the notebooks.

| Notebook | Shows |
|---|---|
| 00_build_data | raw records, filters, map of places |
| 01_sf_stats | counts, categories, Google's Atmosphere tags, vibe words in reviews |
| 02_slang | slang vs. plain words gap table; Urban Dictionary vs. Wiktionary |
| 03_tag_queries | plain vs. slang test queries scored against Google's tags |
| 04_features | lemmas, embeddings, KeyBERT phrases, sentiment on 3 places |

## Data

- [Google Local 2021](https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/) (UCSD McAuley Lab).
  California metadata is downloaded. The 5.35 GB reviews file is streamed, never saved.
  Cite UCTopic (ACL 2022) and Personalized Showcases (SIGIR 2023).
- Urban Dictionary words, Kaggle `therohk/urban-dictionary-words-dataset` (CC0, votes up to 2016).
- English Wiktionary via [kaikki.org](https://kaikki.org/dictionary/) (2026 extract). Only slang/informal senses are kept.

Filters (constants at the top of `src/vibecheck/filter_sf.py`):

- **SF**: inside lat 37.70–37.83, lon -122.52 to -122.35, and the address isn't another city.
  Address alone isn't enough: "South San Francisco" and SFO both match it.
- **Type**: whole-word match on Google categories (cafe, coffee, restaurant, bar, pub, lounge...).
- **Reviews**: non-empty, 50 most recent per place, English part of Google-translated ones.

Data and model files stay out of git.

## Layout

```
src/vibecheck/
  filter_sf.py   data pipeline
  lexicon.py     word lists, gap table, Urban Dictionary lookups
  wiktionary.py  Wiktionary slang senses
  evaluate.py    tag-based test queries and scoring
  plots.py       chart style
  report.py      writes reports/numbers.md
notebooks/       00-04
reports/         numbers.md + charts
tests/
```
