# Ключ и модель читаются из .env, в коде их нет

import os
import sys

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()  # читает файл .env и кладёт значения в os.environ

BASE_URL = "https://openrouter.ai/api/v1"  # OpenRouter принимает тот же формат запросов, что OpenAI
TIMEOUT_SECONDS = 30  # дольше не ждём, чтобы программа не зависла

class LLMError(Exception): #Для пойимки ошибки
    pass


def chat(messages: list[dict], model: str | None = None, temperature: float = 0.0, # функция которая отправляет сообщения модели и возвращает ответ
         json_mode: bool = False) -> dict:
    # Отправляет список сообщений модели, возвращает текст ответа и число токенов
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise LLMError("LLM_API_KEY is not set: copy .env.example to .env and put your key there")
    model = model or os.getenv("LLM_MODEL")  # модель из аргумента, иначе из .env
    if not model:
        raise LLMError("LLM_MODEL is not set in .env")

    client = OpenAI(base_url=BASE_URL, api_key=api_key, timeout=TIMEOUT_SECONDS, max_retries=0)

    extra = {}
    if json_mode:
        extra["response_format"] = {"type": "json_object"}  # просим модель вернуть только JSON

    try:
        response = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature, **extra
        )
    except OpenAIError as error:
        # Нет сети, неверный ключ, кончились деньги, таймаут: всё сюда
        raise LLMError(f"API call failed: {error}") from error

    if not response.choices:
        raise LLMError("API returned no answer")

    usage = response.usage  # расчет сколько токенов ушло, для подсчёта стоимости
    return {
        "text": response.choices[0].message.content or "",
        "model": model,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
    }


if __name__ == "__main__":
    try:
        answer = chat([{"role": "user", "content": "Say hello in one word"}])
    except LLMError as error:
        print(f"Error: {error}")
        sys.exit(1)  # код 1 значит, что программа завершилась с ошибкой
    print(f"Model: {answer['model']}")
    print(f"Answer: {answer['text']}")
    print(f"Tokens: {answer['input_tokens']} in, {answer['output_tokens']} out")
