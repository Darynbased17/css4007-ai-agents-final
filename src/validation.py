# Проверка запроса пользователя и фильтров, которые вернула модель
# Модели не доверяем: каждое значение проверяет код до поиска

from scrape_kn import DISTRICTS

REQUIRED_KEYS = {"district", "rooms", "max_price", "min_floor"}
MIN_ROOMS, MAX_ROOMS = 1, 6
MAX_PRICE_LIMIT = 2_000_000_000
MAX_FLOOR = 50
MAX_REQUEST_LENGTH = 500


class ValidationError(Exception):
    pass


def validate_request_text(text) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValidationError("Request is empty")
    text = text.strip()
    if len(text) > MAX_REQUEST_LENGTH:
        raise ValidationError(f"Request is too long: {len(text)} characters, maximum {MAX_REQUEST_LENGTH}")
    return text


def to_int(value, name: str) -> int:
    # Превращает значение в целое число или выбрасывает ошибку
    if isinstance(value, bool):
        raise ValidationError(f"{name} must be a whole number, got {value!r}")
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)  # модель иногда пишет 45000000.0
    raise ValidationError(f"{name} must be a whole number, got {value!r}")


def validate_filters(filters) -> dict:
    # Проверяет JSON от модели и возвращает чистый словарь фильтров
    if not isinstance(filters, dict):
        raise ValidationError("Filters must be a JSON object")

    missing = REQUIRED_KEYS - filters.keys()
    extra = filters.keys() - REQUIRED_KEYS
    if missing:
        raise ValidationError(f"Missing keys: {sorted(missing)}")
    if extra:
        raise ValidationError(f"Unexpected keys: {sorted(extra)}")

    clean = {}

    district = filters["district"]
    if district is not None and district not in DISTRICTS:
        raise ValidationError(f"Unknown district {district!r}, allowed: {list(DISTRICTS)}")
    clean["district"] = district

    rooms = filters["rooms"]
    if rooms is not None:
        rooms = to_int(rooms, "rooms")
        if not MIN_ROOMS <= rooms <= MAX_ROOMS:
            raise ValidationError(f"rooms must be from {MIN_ROOMS} to {MAX_ROOMS}, got {rooms}")
    clean["rooms"] = rooms

    max_price = filters["max_price"]
    if max_price is not None:
        max_price = to_int(max_price, "max_price")
        if not 0 < max_price <= MAX_PRICE_LIMIT:
            raise ValidationError(f"max_price must be from 1 to {MAX_PRICE_LIMIT}, got {max_price}")
    clean["max_price"] = max_price

    min_floor = filters["min_floor"]
    if min_floor is not None:
        min_floor = to_int(min_floor, "min_floor")
        if not 1 <= min_floor <= MAX_FLOOR:
            raise ValidationError(f"min_floor must be from 1 to {MAX_FLOOR}, got {min_floor}")
    clean["min_floor"] = min_floor

    return clean