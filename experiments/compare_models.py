# Эксперимент недели 11: какая модель лучше переводит запросы в JSON
# 10 запросов с заранее известным правильным ответом, каждая модель получает одни и те же запросы
# Запуск из корня репозитория: python experiments/compare_models.py
# Результат: experiments/week11_model_comparison.csv и итоговая таблица в консоли

import csv
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")  # чтобы import нашёл файлы из папки src

from llm_client import LLMError  # noqa: E402
from parse_request import parse_request  # noqa: E402

# Модели для сравнения : вход, выход

MODELS = {
    "openai/gpt-oss-20b": (0.03, 0.15),
    "google/gemini-2.5-flash-lite": (0.10, 0.40),
}

FIELDS = ["district", "rooms", "max_price", "min_floor"]

# Запрос и правильный ответ: (district, rooms, max_price, min_floor)

TEST_REQUESTS = [
    ("Хочу 2-комнатную в Бостандыкском до 45 млн, не первый этаж", ("Bostandyk", 2, 45000000, 2)),
    ("1-room apartment in Medeu under 30M", ("Medeu", 1, 30000000, None)),
    ("двушка в Ауэзовском районе до 35 миллионов", ("Auezov", 2, 35000000, None)),
    ("трёшка Алмалинский максимум 60 000 000 тенге", ("Almaly", 3, 60000000, None)),
    ("квартира в Турксибе", ("Turksib", None, None, None)),
    ("однокомнатная до 25 млн, не ниже 3 этажа", (None, 1, 25000000, 3)),
    ("4-комнатная в Алатауском до 70 млн, этаж от 5", ("Alatau", 4, 70000000, 5)),
    ("2 комнаты в Жетысуском, бюджет 30 млн", ("Zhetysu", 2, 30000000, None)),
    ("квартира в Бостандыкскм до 40млн", ("Bostandyk", None, 40000000, None)),  # опечатка в районе
    ("Хочу квартиру в Есильском районе", (None, None, None, None)),  # район Астаны, не Алматы
]

OUTPUT_PATH = Path("experiments/week11_model_comparison.csv")


def same(expected, got) -> bool:
    # Сравнивает одно поле: 45000000 и 45000000.0 считаем одинаковыми
    if expected is None or got is None:
        return expected is None and got is None
    if isinstance(expected, int):
        try:
            return float(got) == expected
        except (TypeError, ValueError):
            return False
    return str(got).strip().lower() == expected.lower()


def run() -> None:
    rows = []
    for model, (price_in, price_out) in MODELS.items():
        for text, expected in TEST_REQUESTS:
            row = {"model": model, "request": text, "correct": False, "error": "",
                   "input_tokens": 0, "output_tokens": 0}
            start = time.perf_counter()  # засекаем время ответа
            try:
                result = parse_request(text, model=model)
                got = [result["filters"].get(field) for field in FIELDS]  # get вернёт None, если ключа нет
                row["correct"] = all(same(e, g) for e, g in zip(expected, got))
                row["got"] = got
                row["input_tokens"] = result["input_tokens"]
                row["output_tokens"] = result["output_tokens"]
            except LLMError as error:
                row["error"] = str(error)[:200]  # ошибку записываем, а не падаем
            row["seconds"] = round(time.perf_counter() - start, 2)  # сколько секунд ждали ответ
            row["expected"] = list(expected)
            row["cost_usd"] = (row["input_tokens"] * price_in + row["output_tokens"] * price_out) / 1_000_000
            rows.append(row)
            mark = "OK " if row["correct"] else "BAD"
            print(f"{mark} {model:<30} {text[:45]:<45} {row.get('got', row['error'])}")

    # Сохраняем все ответы, чтобы цифры в отчёте можно было проверить
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        columns = ["model", "request", "expected", "got", "correct", "error",
                   "input_tokens", "output_tokens", "seconds", "cost_usd"]
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    # Итог по каждой модели
    print(f"\n{'model':<30} {'correct':>8} {'errors':>7} {'tokens in/out':>15} {'avg sec':>8} {'cost $':>10}")
    for model in MODELS:
        model_rows = [r for r in rows if r["model"] == model]
        correct = sum(r["correct"] for r in model_rows)  # True считается как 1
        errors = sum(1 for r in model_rows if r["error"])
        tokens_in = sum(r["input_tokens"] for r in model_rows)
        tokens_out = sum(r["output_tokens"] for r in model_rows)
        cost = sum(r["cost_usd"] for r in model_rows)
        avg_seconds = sum(r["seconds"] for r in model_rows) / len(model_rows)
        print(f"{model:<30} {correct:>5}/10 {errors:>7} {tokens_in:>8}/{tokens_out:<6} {avg_seconds:>8.2f} {cost:>10.6f}")
    print(f"\nSaved details to {OUTPUT_PATH}")


if __name__ == "__main__":
    run()