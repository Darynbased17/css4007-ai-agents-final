# Поиск квартир в снимке по проверенным фильтрам
# Ищет код, а не модель: так как результат более точный и проверяемый

import pandas as pd

DEFAULT_LIMIT = 10

RESULT_COLUMNS = [
    "id",
    "district",
    "rooms",
    "area",
    "floor",
    "floors_total",
    "price",
    "price_per_m2",
    "address",
    "url",
]


def search_listings(
    df: pd.DataFrame, filters: dict, limit: int = DEFAULT_LIMIT
) -> list[dict]:
    # df это таблица из load_listings, filters это результат validate_filters
    result = df
    if filters.get("district") is not None:
        result = result[result["district"] == filters["district"]]
    if filters.get("rooms") is not None:
        result = result[result["rooms"] == filters["rooms"]]
    if filters.get("max_price") is not None:
        result = result[result["price"] <= filters["max_price"]]
    if filters.get("min_floor") is not None:
        result = result[result["floor"] >= filters["min_floor"]]

    result = result.sort_values("price_per_m2")
    return result.head(limit)[RESULT_COLUMNS].to_dict("records")
