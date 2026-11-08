"""Scraper for kn.kz apartment listings in Almaty (run offline, once)."""

import csv
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.kn.kz/almaty/prodazha-kvartir"
HEADERS = {"User-Agent": "Mozilla/5.0 (CSS4007 student project)"}
PAGES_PER_DISTRICT = 10
DELAY_SECONDS = 1.5
OUTPUT_PATH = Path("data/listings.csv")


# kn.kz district filter ids (from the site's district links)
DISTRICTS = {
    "Auezov": 7,
    "Bostandyk": 8,
    "Alatau": 14,
    "Almaly": 15,
    "Zhetysu": 16,
    "Medeu": 17,
    "Nauryzbay": 18,
    "Turksib": 19,
}

COLUMNS = [
    "id",
    "district",
    "rooms",
    "price",
    "area",
    "floor",
    "floors_total",
    "year_built",
    "address",
    "url",
]


def fetch_page(district_id: int, page: int) -> str:
    """Функция для того что скачать 1 страниц 1 района в формате .html"""
    params = {"district[]": district_id, "page": page}
    response = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    return response.text


def to_number(text: str) -> float | None:
    """Функция для преображевание из текста в число Пример: '29 500 000 ₸' -> 29500000.0, 'площадь: 40.2 м²' -> 40.2"""
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", "."))
    return float(cleaned) if cleaned else None


def parse_card(card, district: str) -> dict | None:
    "Извлекает список из одной карточки <div data-object-id='...'"
    link = card.select_one('a[href^="/card/"][title]')
    if link is None:
        return None
    title = link.get_text(" ", strip=True).replace("\xa0", " ")
    rooms = re.match(r"(\d+)-комн", title)

    listing = {
        "id": card["data-object-id"],
        "district": district,
        "rooms": int(rooms.group(1)) if rooms else None,
        "price": None,
        "area": None,
        "floor": None,
        "floors_total": None,
        "year_built": None,
        "address": title.split(",", 1)[1].strip() if "," in title else None,
        "url": "https://www.kn.kz" + link["href"],
    }

    for item in card.select("div.text-nowrap"):
        text = item.get_text(" ", strip=True)
        if "этаж" in text:
            floors = re.match(r"(\d+)/(\d+)", text)
            if floors:
                listing["floor"] = int(floors.group(1))
                listing["floors_total"] = int(floors.group(2))
        elif text.startswith("площадь"):
            listing["area"] = to_number(text)
        elif text.startswith("год постройки"):
            year = to_number(text)
            listing["year_built"] = int(year) if year else None

    for span in card.find_all("span"):
        text = span.get_text(strip=True)
        if text.endswith("₸") and "м²" not in text:
            price = to_number(text)
            listing["price"] = int(price) if price else None
            break

    return listing


def parse_page(html: str, district: str) -> list[dict]:
    "Возвращает все объявления, найденные на одной странице"
    soup = BeautifulSoup(html, "html.parser")
    listings = []
    for card in soup.select("div[data-object-id]"):
        listing = parse_card(card, district)
        if listing is not None:
            listings.append(listing)
    return listings


def scrape_all() -> list[dict]:
    "Просматривайеn каждый район страницу за страницей; пропускайtn дубликаты по идентификаторам"
    seen_ids = set()
    rows = []
    for district, district_id in DISTRICTS.items():
        for page in range(1, PAGES_PER_DISTRICT + 1):
            try:
                html = fetch_page(district_id, page)
            except requests.RequestException as error:
                print(f"  {district} page {page}: failed ({error}), skipping district")
                break
            listings = parse_page(html, district)
            new = [l for l in listings if l["id"] not in seen_ids]
            if not new:
                break  # no more pages (or only repeats) for this district
            seen_ids.update(l["id"] for l in new)
            rows.extend(new)
            print(f"{district} page {page}: {len(new)} new, total {len(rows)}")
            time.sleep(DELAY_SECONDS)  # be polite to the site
    return rows


def save_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    rows = scrape_all()
    save_csv(rows, OUTPUT_PATH)
    print(f"Saved {len(rows)} listings to {OUTPUT_PATH}")
