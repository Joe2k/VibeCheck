RUN_NB := uv run jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1
UD_CSV := data/raw/urbandict-word-defs.csv
REVIEWS := data/processed/sf_reviews.parquet

.PHONY: setup data stats features test lint

setup:  ## Create .venv with all dependencies (including spaCy's en_core_web_sm)
	uv sync

data: $(REVIEWS) $(UD_CSV)  ## SF places + reviews (~30 min, streams 5.35 GB) and the Urban Dictionary dump

$(REVIEWS):
	uv run python -m vibecheck.filter_sf

$(UD_CSV):
	uv run kaggle datasets download therohk/urban-dictionary-words-dataset -p data/raw --unzip

stats: data  ## Run the data walkthrough, SF stats and slang notebooks; writes reports/numbers.md
	$(RUN_NB) notebooks/00_build_data.ipynb notebooks/01_sf_stats.ipynb notebooks/02_slang.ipynb

features: data  ## Run the feature prototype on 3 example places
	$(RUN_NB) notebooks/03_features.ipynb

test:
	uv run pytest -q

lint:
	uv run ruff check src tests notebooks && uv run ruff format --check src tests
