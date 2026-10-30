# VibeCheck

A slang-aware search engine for San Francisco cafes, restaurants and bars.
You search the way you talk ("a lowkey aesthetic cafe to grind on some work"), and
VibeCheck matches you against what people actually wrote in Google Maps reviews.

Class project for CS 667 (NLP). This repo currently holds the **data + features** stage:
the San Francisco subset, the stats for our slides, a slang check, and a feature prototype.
The search engine itself comes next.

## Why this needs NLP

Reviewers describe the vibe, but not in the words people search with. Someone types
"boujee", and reviews say "fancy", "upscale" or "classy". Keyword search misses that.
`reports/numbers.md` has the gap table that measures it.

## Setup

You need [uv](https://docs.astral.sh/uv/) (`brew install uv`) and about 4 GB of free disk
for the environment and models.

```bash
make setup      # creates .venv with Python 3.11 and every dependency, including spaCy's en_core_web_sm
make test       # quick unit tests
```

Not using uv? `python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt -e .`
(`requirements.txt` is generated from `uv.lock` with `uv export --no-hashes --no-dev --no-emit-project -o requirements.txt`.)

For the slang notebook you also need a free Kaggle API token:

1. Sign in at kaggle.com, open **Settings -> API -> Create New Token**. This downloads `kaggle.json`.
2. `mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json`

## Running it

```bash
make data       # SF places + reviews (streams the 5.35 GB reviews file, 30-45 min), Urban Dictionary dump
make stats      # runs notebooks 00-02 and writes reports/numbers.md
make features   # runs notebook 03 (downloads ~1 GB of models the first time)
```

Or open the notebooks with `uv run jupyter lab` and run them cell by cell.

| Notebook | What it shows |
|---|---|
| `00_build_data` | Raw records, the SF + category filters, a map of the places, the review filter |
| `01_sf_stats` | Places, reviews, category breakdown, Google's MISC tags (e.g. Atmosphere), how often reviews talk about the vibe |
| `02_slang` | Urban Dictionary slang lexicon and the slang-vs-plain-words gap table |
| `03_features` | spaCy lemmas, mpnet embeddings, KeyBERT vibe phrases and sentiment on 3 example places |

## Data

- **Google Local (2021)**, UCSD McAuley Lab: https://mcauleylab.ucsd.edu/public_datasets/gdrive/googlelocal/
  We use `meta-California.json.gz` (downloaded, 118 MB) and `review-California.json.gz`
  (streamed from the URL, never stored). Please cite UCTopic (Li et al., ACL 2022) and
  Personalized Showcases (Yan et al., SIGIR 2023).
- **Urban Dictionary words** (Kaggle `therohk/urban-dictionary-words-dataset`, CC0, votes as of 2016).

Filtering rules (all tunable at the top of `src/vibecheck/filter_sf.py`):

- **San Francisco**: coordinates inside lat 37.70-37.83 / lon -122.52 to -122.35, and the address
  says "San Francisco, CA" or names no other city (drops the Daly City edge of the box). An address
  match alone isn't enough: it lets in South San Francisco and SFO airport.
- **Cafes, restaurants, bars**: whole-word keyword match on Google's categories.
- **Reviews**: non-empty text, at most the 50 most recent per place. For Google-translated
  reviews, only the English part is kept.

`data/` is gitignored. Never commit data, model files or `kaggle.json`.

## Layout

```
src/vibecheck/   filter_sf.py (data pipeline), lexicon.py (word lists, slang), plots.py, report.py
notebooks/       00-03, run in order
reports/         numbers.md (generated)
tests/           pytest unit tests
data/raw, data/processed   (gitignored)
```
