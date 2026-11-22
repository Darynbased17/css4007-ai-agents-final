# Semester Week 12 Progress Report

## Completed Work

1) Input and output validation (`src/validation.py`): `validate_request_text()` rejects empty requests and requests longer than 500 characters before the model is called; `validate_filters()` checks the model's JSON: exactly 4 keys, district is one of the 8 districts or null, rooms 1–6, max_price 1–2,000,000,000 KZT, min_floor 1–50; `to_int()` accepts 45000000.0 as 45000000 and rejects `true`
2) Retry on invalid model output (`src/parse_request.py`): if the answer is not JSON or fails validation, the model gets its previous answer and the error message and is asked again, at most 2 retries (3 attempts in total), then a clear `LLMError`. Network failures are not retried here (planned for Week 15 guardrails). The model call is passed in as `chat_fn`, so tests can use a fake model
3) Search (`src/search.py`): `search_listings()` filters the CSV snapshot with pandas by district, rooms, maximum price and minimum floor (a `None` filter is skipped), sorts by price per m2 and returns at most 10 apartments
4) Command-line application (`src/app.py`): `run()` connects the whole D-level pipeline (input check → LLM → validation → search → answer) and never crashes
5) First 8 tests (`tests/test_core.py`, `pytest.ini`) with a fake model `FakeLLM` that returns predefined answers and counts calls
6) Setup documentation updated with the app and test commands

## Important Commits

Commit hash: f71305d
Description: Add filter validation and retry on invalid model output
Link: https://github.com/Darynbased17/css4007-ai-agents-final/commit/f71305d

Commit hash: 9f2694a
Description: Add CSV search and command line app
Link: https://github.com/Darynbased17/css4007-ai-agents-final/commit/9f2694a

Commit hash: b5d436d
Description: Add first 8 pytest tests with a fake model
Link: https://github.com/Darynbased17/css4007-ai-agents-final/commit/b5d436d

## Current Functionality

The D-level pipeline works end to end: `python src/app.py "<request>"`. Results with the real model (google/gemini-2.5-flash-lite):

| Request | Filters from the model | Result |
|---|---|---|
| двушка в Бостандыкском до 45 млн, не первый этаж | Bostandyk, 2 rooms, ≤ 45,000,000, floor ≥ 2 | 10 apartments, 612,245–800,000 KZT/m2, all on floor 2 or higher |
| 1-room apartment in Medeu under 30M | Medeu, 1 room, ≤ 30,000,000 | 10 apartments, from 367,847 KZT/m2 |
| трёшка в Медеуском до 15 млн | Medeu, 3 rooms, ≤ 15,000,000 | "No apartments found", suggests a higher budget |
| Хочу квартиру в Есильском районе | all null (Yesil is in Astana) | "No search criteria found" with an example; the CSV is not even loaded |
| двушка | 2 rooms only | 10 cheapest 2-room apartments in the whole city |

Possible answers of `run()`:

| Situation | Answer |
|---|---|
| Empty or too long request | `Invalid request` (the model is not called) |
| API failure or 3 invalid answers | `Sorry, the language model failed` |
| All filters are null | `No search criteria found` |
| Nothing matches | `No apartments found` |
| Otherwise | Up to 10 apartments, cheapest per m2 first |

Tests: `python -m pytest` → 8 passed.

| # | Test | What it proves |
|---|---|---|
| 1 | test_correct_request_is_parsed | A valid answer becomes the right filters in 1 attempt |
| 2 | test_garbage_answer_retries_then_fails | 3 invalid answers → stop with "after 3 attempts", no infinite loop |
| 3 | test_unknown_district_is_rejected | "Yesil" is rejected by validation |
| 4 | test_api_failure_does_not_crash | An API error becomes a clear message, not a crash |
| 5 | test_empty_search_result | No matches → "No apartments found" |
| 6 | test_retry_fixes_bad_answer | "Бостандыкский" is rejected, the retry returns "Bostandyk" in 2 attempts |
| 7 | test_empty_request_does_not_call_model | An empty request costs 0 model calls |
| 8 | test_search_applies_filters | The apartment on floor 1 is filtered out by min_floor = 2 |

## Problems Encountered

1) The model's JSON was trusted without any check: a Russian district name, `"rooms": "two"`, a negative price or missing keys would go straight into the search.
2) Tests that call the real model would cost money, need the internet and could give different answers on different runs.
3) A retry loop can become expensive or endless: every retry sends the whole conversation again, so each attempt uses more input tokens than the previous one.
4) Some results are suspiciously cheap: the cheapest 1-room apartment in Medeu costs 367,847 KZT/m2, less than half of the Medeu 1-room median (786,175), and the cheapest 2-room in the city is 316,788 KZT/m2 in Turksib. These may be real bargains or errors in the listing (wrong area, a share of an apartment).
5) I moved to a new laptop in the middle of the week and had to restore the project from GitHub.

## Solutions

1) Added `validate_filters()` between the model and the search, so only checked values reach the code that works with data.
2) The model call is a parameter (`chat_fn`); the tests pass `FakeLLM`, so they are free, offline and deterministic. A small 3-row table is built inside the tests, so they do not depend on the CSV.
3) The retry loop is bounded (`MAX_RETRIES = 2`) and token usage of all attempts is summed. To check that the test really protects this limit, I changed `MAX_RETRIES` to 5: test 2 failed (the fake model ran out of answers on the 4th call), then I restored 2 and all 8 tests passed again.
4) Not solved yet. Decision for the agent (Week 14): an apartment far below the district median will be reported as "suspiciously cheap, check the listing", not as a good deal.
5) Cloned my fork, created a new virtual environment and a new local `.env`, and set the same git author name and email so the commits stay linked to my account.

## What I Learned

1) The model never sees the data: it only turns text into JSON filters. Filtering, searching and sorting are done by code, and the model's answer is not trusted until code has checked it.
2) "Memory" of the model is the conversation history sent again on every call; that is why a retry costs more than the first attempt.
3) Writing tests with pytest: `assert`, `pytest.raises(..., match=...)`, a fake object with `__call__`, and reading a failing test's traceback from the test down to the line that failed.
4) Python details: set difference for missing and extra keys, chained comparisons `1 <= rooms <= 6`, `bool` being a subclass of `int`, `float.is_integer()`, `!r` in f-strings.
5) pandas boolean filtering, `sort_values`, `head`, `to_dict("records")`.
6) Restoring a project on a new computer: clone, virtual environment, local `.env`, git author identity.

## Next Week

1) Tool calling (level C): turn `search_listings`, `get_district_stats`, `estimate_price` and `calculate` into tools that the model chooses by itself.
2) A dispatcher that validates tool arguments before running a tool, a permission table (read-only tools), and a log of every tool call.
3) `estimate_price`: median price per m2 of the district and room group × area, with the fallback to the district median when a group has fewer than 5 listings.
4) Support questions that need no tools.
5) More tests: correct tool choice, invalid tool arguments rejected, tool error does not make the model invent an answer.
6) Ask the instructor (not asked yet): is the topic accepted for level A, can I use my own scraped CSV snapshot, can I write my own agent loop without LangGraph.