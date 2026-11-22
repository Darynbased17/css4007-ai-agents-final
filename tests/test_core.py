# Тесты уровня D: поддельная модель вместо настоящей
# Тесты бесплатные, без сети и всегда дают одинаковый результат

import pandas as pd
import pytest

from app import run
from llm_client import LLMError
from parse_request import parse_request
from validation import ValidationError, validate_filters

GOOD_JSON = '{"district": "Bostandyk", "rooms": 2, "max_price": 45000000, "min_floor": 2}'


class FakeLLM:
    # Поддельная модель: отдаёт заранее заданные ответы по очереди и считает вызовы
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def __call__(self, messages, **kwargs):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply  # так имитируем сбой API
        return {"text": reply, "model": "fake", "input_tokens": 10, "output_tokens": 5}


def small_table():
    # Маленькая таблица вместо настоящего CSV, чтобы тест не зависел от данных
    df = pd.DataFrame([
        {"id": "1", "district": "Bostandyk", "rooms": 2, "area": 50.0, "floor": 3, "floors_total": 9,
         "price": 40_000_000, "address": "a", "url": "u1"},
        {"id": "2", "district": "Bostandyk", "rooms": 2, "area": 60.0, "floor": 1, "floors_total": 5,
         "price": 42_000_000, "address": "b", "url": "u2"},
        {"id": "3", "district": "Medeu", "rooms": 1, "area": 35.0, "floor": 4, "floors_total": 12,
         "price": 30_000_000, "address": "c", "url": "u3"},
    ])
    df["price_per_m2"] = df["price"] / df["area"]
    return df


# 1. Правильный запрос превращается в правильные фильтры
def test_correct_request_is_parsed():
    fake = FakeLLM([GOOD_JSON])
    result = parse_request("двушка в Бостандыкском до 45 млн, не первый этаж", chat_fn=fake)
    assert result["filters"] == {"district": "Bostandyk", "rooms": 2, "max_price": 45000000, "min_floor": 2}
    assert result["attempts"] == 1


# 2. Модель всё время отвечает мусором: 3 попытки, потом понятная ошибка, а не бесконечный цикл
def test_garbage_answer_retries_then_fails():
    fake = FakeLLM(["sorry, I cannot help", "still not json", "{broken"])
    with pytest.raises(LLMError, match="after 3 attempts"):
        parse_request("двушка в Бостандыкском", chat_fn=fake)
    assert fake.calls == 3


# 3. Неизвестный район отклоняется проверкой
def test_unknown_district_is_rejected():
    with pytest.raises(ValidationError, match="Unknown district"):
        validate_filters({"district": "Yesil", "rooms": 2, "max_price": None, "min_floor": None})


# 4. Сбой API: программа не падает, а возвращает понятное сообщение
def test_api_failure_does_not_crash():
    fake = FakeLLM([LLMError("API call failed: Connection error")])
    answer = run("двушка в Бостандыкском", chat_fn=fake, df=small_table())
    assert answer.startswith("Sorry, the language model failed")


# 5. Ничего не найдено: понятное сообщение вместо пустой таблицы
def test_empty_search_result():
    fake = FakeLLM(['{"district": "Medeu", "rooms": 3, "max_price": 10000000, "min_floor": null}'])
    answer = run("трёшка в Медеуском до 10 млн", chat_fn=fake, df=small_table())
    assert answer.startswith("No apartments found")


# 6. Плохой первый ответ исправляется повтором
def test_retry_fixes_bad_answer():
    fake = FakeLLM(['{"district": "Бостандыкский", "rooms": 2, "max_price": 45000000, "min_floor": 2}', GOOD_JSON])
    result = parse_request("двушка в Бостандыкском", chat_fn=fake)
    assert result["filters"]["district"] == "Bostandyk"
    assert result["attempts"] == 2


# 7. Пустой запрос отклоняется до вызова модели, токены не тратятся
def test_empty_request_does_not_call_model():
    fake = FakeLLM([GOOD_JSON])
    answer = run("   ", chat_fn=fake, df=small_table())
    assert answer.startswith("Invalid request")
    assert fake.calls == 0


# 8. Поиск применяет все фильтры: квартира на 1 этаже отсеяна
def test_search_applies_filters():
    fake = FakeLLM([GOOD_JSON])
    answer = run("двушка в Бостандыкском до 45 млн, не первый этаж", chat_fn=fake, df=small_table())
    assert "Found 1" in answer
    assert "u1" in answer and "u2" not in answer