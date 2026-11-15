# Перевод запроса покупателя в JSON-фильтры для поиска квартир
# Модель только переводит текст в JSON, искать будет код

import json
import sys

from llm_client import LLMError, chat
from scrape_kn import DISTRICTS 

SYSTEM_PROMPT = f"""You convert an apartment buyer's request in Almaty into JSON search filters.
The request can be in Russian or English.

Return ONLY a JSON object with exactly these keys:
- "district": one of {list(DISTRICTS)} or null
- "rooms": integer number of rooms or null
- "max_price": maximum price in KZT as an integer or null
- "min_floor": lowest acceptable floor as an integer or null

District names in Russian: Ауэзовский = Auezov, Бостандыкский = Bostandyk, Алатауский = Alatau,
Алмалинский = Almaly, Жетысуский = Zhetysu, Медеуский = Medeu, Наурызбайский = Nauryzbay,
Турксибский = Turksib.

Rules:
- "млн" or "M" means million: "45 млн" -> 45000000
- "однушка" = 1 room, "двушка" = 2 rooms, "трёшка" = 3 rooms
- "не первый этаж" or "not the first floor" -> "min_floor": 2
- If the district is not one of the 8 districts above, use null
- If something is not mentioned, use null. Never invent values

Example:
Request: Хочу 2-комнатную в Бостандыкском до 45 млн, не первый этаж
Answer: {{"district": "Bostandyk", "rooms": 2, "max_price": 45000000, "min_floor": 2}}"""


def extract_json(text: str) -> dict:
    # Достаёт JSON из ответа модели
    # Некоторые модели оборачивают JSON в ```json ... ```, поэтому берём текст от первой { до последней }
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise LLMError(f"Model did not return JSON: {text[:100]}")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as error:
        raise LLMError(f"Model returned broken JSON: {error}") from error


def parse_request(text: str, model: str | None = None) -> dict:
    # Текст пользователя -> словарь фильтров и число токенов
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": text},
    ]
    answer = chat(messages, model=model, temperature=0.0, json_mode=True)
    filters = extract_json(answer["text"])
    return {
        "filters": filters,
        "input_tokens": answer["input_tokens"],
        "output_tokens": answer["output_tokens"],
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python src/parse_request.py "your request"')
        sys.exit(1)
    request_text = sys.argv[1]
    try:
        result = parse_request(request_text)
    except LLMError as error:
        print(f"Error: {error}")
        sys.exit(1)
    print(json.dumps(result["filters"], ensure_ascii=False, indent=2))
    print(f"Tokens: {result['input_tokens']} in, {result['output_tokens']} out")