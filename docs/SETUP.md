# Almaty Apartment Analyst — Setup and Run

## Requirements

- Python 3.10 or newer
- An OpenRouter API key (https://openrouter.ai)
- Node.js 22+ only for the course report checks (`npm run ...`)

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Create your local `.env` from the template and put your key there:

```bash
cp .env.example .env        # Windows PowerShell: Copy-Item .env.example .env
```

```
LLM_API_KEY=sk-or-...
LLM_MODEL=google/gemini-2.5-flash-lite
```

`.env` is listed in `.gitignore` and must never be committed. `.env.example` stays empty of secrets.

## Run

All commands are run from the repository root.

| Command | What it does |
|---|---|
| `python src/stats.py` | Loads `data/listings.csv`, cleans it, prints median price per m2 by district and room count |
| `python src/llm_client.py` | Checks the API connection with a one-word request |
| `python src/app.py "двушка в Бостандыкском до 45 млн, не первый этаж"` | **Main app:** request -> LLM -> validation -> search in the CSV -> up to 10 apartments, cheapest per m2 first |
| `python -m pytest` | Runs the tests (fake model, no network, no cost) |
| `python src/parse_request.py "двушка в Бостандыкском до 45 млн, не первый этаж"` | Converts a buyer request (Russian or English) into validated JSON search filters |
| `python experiments/compare_models.py` | Runs 10 labelled requests on each model; saves accuracy, tokens, latency and cost to `experiments/week11_model_comparison.csv` |
| `python src/scrape_kn.py` | Re-collects the data snapshot from kn.kz (about 3 minutes; not needed, the snapshot is already in the repository) |

## Project structure

```
data/listings.csv            snapshot of 2,400 kn.kz listings (8 districts x 300), collected 2026-11-08
src/scrape_kn.py             offline scraper: kn.kz pages -> data/listings.csv
src/stats.py                 load_listings() and district_stats()
src/llm_client.py            chat(): OpenRouter call, token usage, LLMError on any failure
src/parse_request.py         parse_request(): user text -> validated JSON filters, up to 2 retries
src/validation.py            validate_request_text(), validate_filters(), ValidationError
src/search.py                search_listings(): filters -> apartments from the CSV
src/app.py                   run(): the full pipeline, never crashes
tests/test_core.py           8 tests with a fake model (FakeLLM)
experiments/compare_models.py  model comparison experiment (Week 11)
reports/                     proposal and weekly reports
```

## Data

The snapshot contains only apartment attributes: id, district, rooms, price, area, floor, floors_total, year_built, address, url. Phone numbers, names and seller details are not collected. The agent works only with this saved snapshot, never with the live site, so results are reproducible.

## Use of AI assistance

Claude (Anthropic) is used as a tutor: it explains topics, suggests code structure and reviews my code. I run every script myself, check the results, and can explain every line. Parts written with its help are discussed line by line in the weekly reports.