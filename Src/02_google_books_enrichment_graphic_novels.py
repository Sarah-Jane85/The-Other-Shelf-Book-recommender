"""
02 Description Enrichment — Graphic Novels

Goal:
Add book descriptions from Open Library work pages.

Run from the project root:
    python Src/02_google_books_enrichment_graphic_novels.py

Input:
    Data/Raw/graphic_novels/openlibrary_graphic_novels_raw.csv

Output:
    Data/Clean/graphic_novels_with_descriptions.csv
"""

from pathlib import Path
import time

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "Data" / "Raw" / "graphic_novels" / "openlibrary_graphic_novels_raw.csv"
CLEAN_DIR = ROOT / "Data" / "Clean"
OUTPUT_PATH = CLEAN_DIR / "graphic_novels_with_descriptions.csv"


def fetch_openlibrary_description(ol_key: str) -> str | None:
    """Fetch a description from an Open Library work key such as /works/OL123W."""
    if pd.isna(ol_key):
        return None

    try:
        url = f"https://openlibrary.org{ol_key}.json"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        data = response.json()
        description = data.get("description")

        if isinstance(description, dict):
            return description.get("value")
        if isinstance(description, str):
            return description
        return None

    except Exception:
        return None


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(RAW_PATH)
    print(f"Loaded raw rows: {len(df):,}")

    descriptions = []
    for i, key in enumerate(df["ol_key"]):
        descriptions.append(fetch_openlibrary_description(key))

        if i % 100 == 0:
            print(f"Processed {i:,} / {len(df):,}")
        time.sleep(0.2)

    df["description"] = descriptions
    print(f"Missing descriptions: {df['description'].isna().sum():,}")

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved enriched data to: {OUTPUT_PATH}")
    print(f"Rows saved: {len(df):,}")


if __name__ == "__main__":
    main()
