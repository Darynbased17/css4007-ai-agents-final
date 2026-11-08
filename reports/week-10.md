# Semester Week 10 Progress Report

## Completed Work


1) Forked the instructor repository, chose the topic (Almaty Apartment Analyst) and level A.
2) Wrote reports/proposal.md: problem, users, 13 proposed functions, 5 agent tools with a permission table, model choice (OpenRouter), architecture diagram, 6 example requests, evaluation plan with 14 planned tests (4 guardrail tests), and milestones for Weeks 10–17.
3) Studied the structure of kn.kz listing pages and wrote src/scrape_kn.py, an offline scraper (requests + BeautifulSoup) that collects apartments for sale in the 8 city districts of Almaty.
4) Collected the first data snapshot: 2,400 listings (8 districts × 10 pages × 30 listings) in data/listings.csv with columns id, district, rooms, price, area, floor, floors_total, year_built, address, url.

## Important Commits

Commit hash: 0a167b6
Description: Add project proposal: Almaty apartment analyst agent (level A)
Link: https://github.com/Darynbased17/css4007-ai-agents-final/commit/0a167b6

Commit hash: 8ee70df
Description: Add kn.kz scraper: 8 Almaty districts, 2400 listings to CSV
Link: https://github.com/Darynbased17/css4007-ai-agents-final/commit/8ee70df

## Current Functionality

1) python src/scrape_kn.py downloads 10 pages per district with a 1.5 s delay between requests, parses each listing card, removes duplicates by listing id, and saves the result to data/listings.csv.
2) Network errors do not crash the scraper: the failed district is skipped and the rest are still collected.
3) Only apartment attributes are saved. Phone numbers, names and seller details are not stored.
4) No LLM integration yet (planned for Week 11).

## Problems Encountered

1) Listing cards on kn.kz have no separate "district" field; the district only appears in the page filter.
2) Values are stored as text with spaces and units ("29 500 000 ₸", "площадь: 40.2 м²", "1/5 этаж"), and addresses contain non-breaking spaces.
3) My first run crashed at the very end with ValueError: dict contains fields not in fieldnames: 'area', so the scraped data was not saved.

## Solutions

1) Scraped each district separately through the site's filter (?district[]=<id>), so the district is known from the request itself.
2) Wrote to_number(), which removes everything except digits and the decimal point, and used regular expressions for the floor and room count.
3) The crash came from my COLUMNS list: I had duplicated rooms and price and missed area. I fixed the list so it matches the keys returned by parse_card() and ran the scraper again.
4) Decided to work with a saved CSV snapshot instead of live scraping, so tests and the demo do not depend on the site.

## What I Learned

1) How a server-rendered HTML page is structured and how to find data with CSS selectors in BeautifulSoup (select, select_one, attribute selectors).
2) requests.get with params, headers, timeout and raise_for_status(); why a delay between requests matters
3) Basic regular expressions (re.match, re.sub) for turning text into numbers

## Next Week

1) Integrate initial LLM request: user text → JSON search filters
2) Load and clean the CSV with pandas and compute the median price per m² by district and room count
3) Set up the OpenRouter client with the key
4) Maybe add README