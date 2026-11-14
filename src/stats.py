#Load the listings snapshot, clean it, and compute market statistics

from pathlib import Path

import pandas as pd

DATA_PATH = Path("data/listings.csv")

# Acceptable cleaning limits
MIN_AREA, MAX_AREA = 15, 500 # m2
MIN_YEAR, MAX_YEAR = 1900, 2030
MIN_PRICE_PER_M2, MAX_PRICE_PER_M2 = 150_000, 5_000_000   # KZT per m2
MAX_ROOMS_GROUP = 4   # 4, 5, 6, 7 rooms are grouped as "4+" (too few listings)


def load_listings(path: Path = DATA_PATH) -> pd.DataFrame:
    """Read the CSV, remove broken rows and add price_per_m2 and rooms_group."""
    df = pd.read_csv(path)
    rows_before = len(df)

    df = df.dropna(subset=["price", "area", "rooms", "district"])
    df = df[(df["area"] >= MIN_AREA) & (df["area"] <= MAX_AREA)]
    df = df[df["floor"] >= 1]

    # A wrong build year does not make the price wrong so we keep the row by droping the year
    bad_year = (df["year_built"] < MIN_YEAR) | (df["year_built"] > MAX_YEAR)
    df.loc[bad_year, "year_built"] = None

    df["price_per_m2"] = df["price"] / df["area"]
    df = df[df["price_per_m2"].between(MIN_PRICE_PER_M2, MAX_PRICE_PER_M2)]

    df["rooms_group"] = df["rooms"].clip(upper=MAX_ROOMS_GROUP)

    print(f"Loaded {rows_before} rows, kept {len(df)} after cleaning")
    return df

# Median price per m2 and number of listings for each district × rooms group
def district_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = (
        df.groupby(["district", "rooms_group"])["price_per_m2"]
        .agg(median_price_per_m2="median", listings="count")
        .reset_index()
    )
    stats["median_price_per_m2"] = stats["median_price_per_m2"].round(0)
    return stats


if __name__ == "__main__":
    listings = load_listings()
    table = district_stats(listings)
    print(table.to_string(index=False))

    by_district = listings.groupby("district")["price_per_m2"].median().sort_values()
    print("\nMedian price per m² by district (cheapest first):")
    for district, value in by_district.items():
        print(f"  {district:<10} {value:>12,.0f} KZT/m²")
