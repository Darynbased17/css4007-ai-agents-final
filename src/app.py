# Приложение уровня D: запрос текстом -> модель -> проверка -> поиск в CSV -> ответ

import sys

from llm_client import LLMError, chat
from parse_request import parse_request
from search import search_listings
from stats import load_listings
from validation import ValidationError


def format_listing(listing: dict) -> str:
    # Одна квартира в одну строку
    return (
        f"{listing['district']:<10} {listing['rooms']}-room {listing['area']:>6.1f} m2  "
        f"floor {listing['floor']}/{listing['floors_total']}  "
        f"{listing['price']:>13,} KZT  {listing['price_per_m2']:>10,.0f} KZT/m2  {listing['url']}"
    )


def run(text: str, chat_fn=chat, df=None) -> str:
    try:
        parsed = parse_request(text, chat_fn=chat_fn)
    except ValidationError as error:
        return f"Invalid request: {error}"
    except LLMError as error:
        return f"Sorry, the language model failed: {error}"

    filters = parsed["filters"]
    if all(value is None for value in filters.values()):
        return "No search criteria found. Example: 2-room in Bostandyk up to 45M, not the first floor"

    if df is None:
        df = load_listings()
    found = search_listings(df, filters)
    if not found:
        return f"No apartments found for {filters}. Try a higher budget or another district"

    lines = [f"Filters: {filters}", f"Found {len(found)} (cheapest per m2 first):"]
    lines += [format_listing(listing) for listing in found]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python src/app.py "your request"')
        sys.exit(1)
    print(run(sys.argv[1]))
