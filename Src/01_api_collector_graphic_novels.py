"""
01 API Collector — Graphic Novels

Goal:
Collect a large raw dataset of graphic novel / comics-related books using the
Open Library API.

Run from the project root:
    python Src/01_api_collector_graphic_novels.py

Output:
    Data/Raw/graphic_novels/openlibrary_graphic_novels_raw.csv
"""

from pathlib import Path
import time

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "Data" / "Raw" / "graphic_novels"
CLEAN_DIR = ROOT / "Data" / "Clean"
OUTPUT_PATH = RAW_DIR / "openlibrary_graphic_novels_raw.csv"

SEARCH_TERMS = [
    "graphic novel",
    "graphic novels",
    "sequential art",
    "graphic memoir",
    "literary comics",
    "adult graphic novel",
    "illustrated novel",
    "visual storytelling",
    "graphic biography",
    "graphic history",
]


def fetch_openlibrary_books(search_term: str, pages: int = 10, pause: float = 0.5) -> list[dict]:
    """Fetch book search results from Open Library for one search term."""
    books = []

    for page in range(1, pages + 1):
        url = "https://openlibrary.org/search.json"
        params = {"q": search_term, "page": page}

        try:
            response = requests.get(url, params=params, timeout=20)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"Failed for '{search_term}', page {page}: {exc}")
            continue

        data = response.json()
        docs = data.get("docs", [])

        for doc in docs:
            books.append(
                {
                    "search_term": search_term,
                    "ol_key": doc.get("key"),
                    "title": doc.get("title"),
                    "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else None,
                    "first_publish_year": doc.get("first_publish_year"),
                    "publisher": ", ".join(doc.get("publisher", [])[:3]) if doc.get("publisher") else None,
                    "language": ", ".join(doc.get("language", [])[:5]) if doc.get("language") else None,
                    "subject": ", ".join(doc.get("subject", [])[:30]) if doc.get("subject") else None,
                    "isbn": doc.get("isbn", [None])[0] if doc.get("isbn") else None,
                    "cover_i": doc.get("cover_i"),
                }
            )

        print(f"Fetched {len(docs)} books for '{search_term}' page {page}")
        time.sleep(pause)

    return books


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    all_books = []
    for term in SEARCH_TERMS:
        all_books.extend(fetch_openlibrary_books(term, pages=10))

    raw_df = pd.DataFrame(all_books)
    print(f"Raw rows collected: {len(raw_df):,}")

    raw_df = raw_df.drop_duplicates(subset=["title", "author"])
    print(f"Rows after title/author dedupe: {len(raw_df):,}")

    raw_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved raw data to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
