# Semester Week 11 Progress Report

## Completed Work

1) Data cleaning and market statistics (src/stats.py): load_listings() removes broken rows and adds price_per_m2 and rooms_group; district_stats() computes the median price per m2 and the number of listings for every district × rooms group. 2,397 of 2,400 listings remain after cleaning.
2) First working LLM integration (src/llm_client.py): chat() calls OpenRouter through the OpenAI-compatible API, reads the key and model from .env, returns the answer with token usage, and turns every failure (no key, network error, timeout, empty answer) into one LLMError, so the program never crashes with a traceback.
3) First LLM feature (src/parse_request.py): parse_request() converts a buyer request in Russian or English into JSON filters {district, rooms, max_price, min_floor} using a system prompt with the 8 district names, conversion rules and one example; temperature=0 and JSON mode.
4) Model comparison experiment (experiments/compare_models.py): 10 labelled requests, 2 models, automatic scoring against the expected answer; accuracy, tokens, latency and cost saved to experiments/week11_model_comparison.csv.
5) Setup and run documentation (docs/SETUP.md), requirements.txt, data/raw/ added to .gitignore.

## Important Commits

Commit hash: 0252288
Description: Add data cleaning and district price statistics 
Link: https://github.com/Darynbased17/css4007-ai-agents-final/commit/0252288

Commit hash: e96e375 
Description: Add OpenRouter client and first LLM request: text to JSON filters 
Link: https://github.com/Darynbased17/css4007-ai-agents-final/commit/e96e375

Commit hash: 0d240ed Description: 
Add model comparison experiment and setup documentation 
Link: https://github.com/Darynbased17/css4007-ai-agents-final/commit/0d240ed

## Current Functionality

1) python src/stats.py prints the market table. Median price per m2 by district: Turksib 632,973 KZT (cheapest), Alatau 675,105, Zhetysu 681,099, Nauryzbay 683,333, Auezov 758,079, Almaly 885,922, Medeu 935,565, Bostandyk 950,704 KZT (most expensive, 1.5 × Turksib)

2) When run the src/parse_request.py with sentence "двушка в Бостандыкском до 45 млн, не первый этаж" LLM returns {"district": "Bostandyk", "rooms": 2, "max_price": 45000000, "min_floor": 2}

3) Model comparison results (10 requests per model, run on 2026-11-15): Compered google/gemini-2.5-flash-lite and openai/gpt-oss-20b

Model	| Correct |	Errors | Tokens in / out | Avg latency | Cost of 10 requests
openai/gpt-oss-20b	| 10/10 |	0 |	4,908 / 1,663 |	2.45 s |	$0.000397
google/gemini-2.5-flash-lite	| 10/10	| 0	| 4,142 / 340	| 1.23 s	| $0.000550

* Selected model: google/gemini-2.5-flash-lite (see Solutions).
* What is not implemented: validation of filter values, retry on bad JSON, search in the CSV (Week 12)

## Problems Encountered

1) Both models scored 10/10, so the experiment could not tell them apart by accuracy
2) gpt-oss-20b produced about 5 times more output tokens (1,663 vs 340) and needed even 67 output tokens to answer "Say hello in one word"
3) Data contained broken rows: floor 0, build year 1684, area under 15 m2. Groups with 5–7 rooms had only 1–3 listings, and Alatau "4+" has only 2 listings, so a median there is not reliable

## Solutions

1) Added a latency measurement (time.perf_counter()) to the experiment, so the choice is based on a second measured criterion. Next week the request set will include harder cases
2) The extra tokens are reasoning tokens: gpt-oss-20b "thinks" before answering, and these tokens are billed as output. Its tokens are cheaper, so it is still cheaper overall, but it was 2 times slower (2.45 s vs 1.23 s per request)
3) Cleaning rules in load_listings(): keep area 15–500 m2 and floor ≥ 1; a wrong build year is set to empty instead of deleting the row (the price is still valid); 4–7 rooms are grouped as "4+". Decision for Week 12: if a group has fewer than 5 listings, estimate_price will use the median of the whole district
4) Model decision: google/gemini-2.5-flash-lite. Accuracy is equal; the difference in cost is $0.000016 per request. but the agent in Weeks 13–15 will call the model 5–12 times per goal, so being 2 times faster matters more than the small price difference


## What I Learned

1) Calling an LLM from Python through an OpenAI-compatible API (base_url), and keeping secrets in .env with python-dotenv instead of in code.
2) Writing one custom exception (LLMError) so that every API failure is handled in one place.
3) How a system prompt with rules and one example (few-shot) makes structured output reliable; why temperature=0 is used for parsing.
4) Reasoning models spend extra output tokens on thinking, which changes both cost and latency.
5) pandas: read_csv, boolean filtering, between, clip, groupby + agg, and why the median is more robust than the mean for prices with outliers.
6) An experiment needs labelled data and saved raw results; a test set where every model scores 100% does not discriminate between models.

## Next Week

1) Implement core functionality
2) Validate the parsed filters in code: district from the list of 8, rooms 1–6, price > 0, floor ≥ 1
3) Retry when the model returns invalid JSON (at most 2 retries), then a clear error message
4) search_listings() over the CSV with the validated filters
5) First 5 pytest tests with a mock model (no network, no cost): correct parsing, garbage → retry → error, unknown district, API failure, empty search result
6) Harder request set for the experiment (ranges like "3–4 rooms", "45.5 млн", vague places)
