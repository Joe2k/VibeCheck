RUN_NB := uv run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1
UD_CSV := data/raw/urbandict-word-defs.csv
REVIEWS := data/processed/sf_reviews.parquet
WIKI := data/processed/wiktionary_slang.parquet

.PHONY: setup data stats features test lint

setup:  ## Create .venv with all dependencies (including spaCy's en_core_web_sm)
	uv sync

data: $(REVIEWS) $(UD_CSV) $(WIKI)  ## SF places + reviews, Urban Dictionary, Wiktionary slang (~1 h, mostly streaming)

$(REVIEWS):
	uv run python -m vibecheck.filter_sf

$(UD_CSV):
	uv run kaggle datasets download therohk/urban-dictionary-words-dataset -p data/raw --unzip

WIKI_RAW := data/raw/kaikki-English.jsonl.gz

$(WIKI): $(WIKI_RAW)
	uv run python -m vibecheck.wiktionary

$(WIKI_RAW):  # resumable: the server stalls, so re-running continues where it stopped
	curl -L -C - --retry 10 --speed-limit 1000 --speed-time 60 -o $@.part https://kaikki.org/dictionary/English/kaikki.org-dictionary-English.jsonl.gz
	mv $@.part $@

stats: data  ## Notebooks 00-03; writes reports/numbers.md
	$(RUN_NB) notebooks/00_build_data.ipynb notebooks/01_sf_stats.ipynb notebooks/02_slang.ipynb notebooks/03_tag_queries.ipynb

features: data  ## Notebook 04: feature prototype on 3 places
	$(RUN_NB) notebooks/04_features.ipynb

test:
	uv run pytest -q

lint:
	uv run ruff check src tests notebooks && uv run ruff format --check src tests
