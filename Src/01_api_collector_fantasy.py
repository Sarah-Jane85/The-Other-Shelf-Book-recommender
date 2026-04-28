"""
01_api_collector_fantasy.py
────────────────────────────
Collects non-western fantasy books from the Open Library API.

Uses 52 genre-subject queries targeting specific cultural traditions
(e.g. 'fantasy yoruba', 'fantasy djinn', 'wuxia', 'afrofuturism').
Includes checkpoint/resume functionality for rate-limit safety.

Usage:
    python 01_api_collector_fantasy.py

Output:
    Data/Raw/non_western_fantasy/ol_genre_first.json
"""

import requests
import json
import time
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).resolve().parents[2]
RAW_DIR    = REPO_ROOT / "Data" / "Raw" / "non_western_fantasy"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH   = RAW_DIR / "ol_genre_first.json"
CKPT_PATH  = RAW_DIR / "ol_genre_first_checkpoint.json"

# ── Query list ────────────────────────────────────────────────────────────────
# Each tuple: (search_query, source_tag)
GENRE_SUBJECT_QUERIES = [
    # Africa
    ("fantasy africa",                "africa"),
    ("fantasy african",               "africa"),
    ("science fiction africa",        "africa"),
    ("fantasy yoruba",                "yoruba"),
    ("fantasy igbo",                  "igbo"),
    ("fantasy akan",                  "akan"),
    ("fantasy zulu",                  "zulu"),
    ("fantasy orisha",                "orisha"),
    ("fantasy anansi",                "anansi"),
    ("afrofuturism",                  "afrofuturism"),
    ("africanfuturism",               "afrofuturism"),
    # East Asia
    ("fantasy chinese",               "chinese"),
    ("fantasy japan",                 "japanese"),
    ("fantasy japanese",              "japanese"),
    ("fantasy korean",                "korean"),
    ("wuxia",                         "wuxia"),
    ("xianxia",                       "xianxia"),
    ("fantasy yokai",                 "japanese"),
    ("fantasy kitsune",               "japanese"),
    ("fantasy cultivation",           "chinese"),
    # South / Southeast Asia
    ("fantasy india",                 "south_asian"),
    ("fantasy indian",                "south_asian"),
    ("fantasy hindu mythology",       "south_asian"),
    ("fantasy mahabharata",           "south_asian"),
    ("fantasy ramayana",              "south_asian"),
    ("fantasy philippine",            "filipino"),
    ("fantasy filipino",              "filipino"),
    ("fantasy aswang",                "filipino"),
    ("fantasy vietnamese",            "southeast_asian"),
    ("fantasy thai",                  "southeast_asian"),
    # Middle East / Persian
    ("fantasy arabian",               "middle_eastern"),
    ("fantasy djinn",                 "middle_eastern"),
    ("fantasy persian",               "middle_eastern"),
    ("fantasy islamic",               "middle_eastern"),
    ("fantasy ottoman",               "middle_eastern"),
    ("fantasy mughal",                "south_asian"),
    # Latin America
    ("fantasy aztec",                 "latin_american"),
    ("fantasy maya",                  "latin_american"),
    ("fantasy mayan",                 "latin_american"),
    ("fantasy inca",                  "latin_american"),
    ("fantasy latin american",        "latin_american"),
    ("science fiction latin american","latin_american"),
    ("fantasy curandera",             "latin_american"),
    ("fantasy mesoamerican",          "latin_american"),
    # Indigenous Americas
    ("fantasy native american",       "indigenous_americas"),
    ("fantasy indigenous",            "indigenous_americas"),
    ("fantasy navajo",                "indigenous_americas"),
    ("fantasy lakota",                "indigenous_americas"),
    # Oceania
    ("fantasy maori",                 "oceania"),
    ("fantasy aboriginal",            "oceania"),
    ("fantasy pacific islander",      "oceania"),
    ("fantasy polynesian",            "oceania"),
]

PAGE_LIMIT = 20    # max pages per query (100 results/page)
DELAY      = 0.5   # seconds between requests


# ── API functions ─────────────────────────────────────────────────────────────
def fetch_ol_page(query: str, page: int = 1) -> dict:
    """Fetch one page of results from the Open Library search API."""
    r = requests.get(
        "https://openlibrary.org/search.json",
        params={
            "q":      query,
            "fields": "title,author_name,first_publish_year,cover_i,"
                      "ratings_average,ratings_count,subject,key",
            "limit":  100,
            "offset": (page - 1) * 100,
        },
        timeout=20
    )
    r.raise_for_status()
    return r.json()


def to_record(doc: dict, tag: str, query: str) -> dict:
    """Convert a raw Open Library API document to a standardized record."""
    cover_i = doc.get("cover_i")
    return {
        "title":          doc.get("title", "").strip(),
        "author":         (doc.get("author_name") or [""])[0],
        "year_published": doc.get("first_publish_year"),
        "cover_url":      f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
                          if cover_i else "",
        "avg_rating":     doc.get("ratings_average"),
        "num_ratings":    doc.get("ratings_count"),
        "subjects":       doc.get("subject", []),
        "source":         "open_library",
        "source_url":     f"https://openlibrary.org{doc.get('key', '')}",
        "source_tag":     tag,
        "query":          query,
        "description":    "",
    }


# ── Main scrape loop ──────────────────────────────────────────────────────────
def main():
    # Resume from checkpoint if available
    if CKPT_PATH.exists():
        with open(CKPT_PATH) as f:
            all_books = json.load(f)
        done_queries = {b.get("query") for b in all_books if b.get("query")}
        print(f"Resuming — {len(all_books):,} books, {len(done_queries)} queries done")
    else:
        all_books    = []
        done_queries = set()
        print("Starting fresh")

    seen_keys = {b["source_url"] for b in all_books}

    for query, tag in GENRE_SUBJECT_QUERIES:
        if query in done_queries:
            print(f"  ⏭  Skipping: {query}")
            continue

        print(f"\n── {query} ({tag}) ──")
        page_num  = 1
        query_new = 0

        while page_num <= PAGE_LIMIT:
            try:
                data = fetch_ol_page(query, page_num)
                docs = data.get("docs", [])
                if not docs:
                    break

                for doc in docs:
                    key = f"https://openlibrary.org{doc.get('key', '')}"
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    rec = to_record(doc, tag, query)
                    if rec["title"]:
                        all_books.append(rec)
                        query_new += 1

                print(f"  Page {page_num}: {len(docs)} results | "
                      f"{query_new} new | total: {len(all_books):,}")

                if len(docs) < 100:
                    break

                page_num += 1
                time.sleep(DELAY)

            except Exception as e:
                print(f"  ❌ Error on page {page_num}: {e}")
                time.sleep(5)
                break

        # Save checkpoint after every query
        with open(CKPT_PATH, "w") as f:
            json.dump(all_books, f)

    # Final save
    with open(OUT_PATH, "w") as f:
        json.dump(all_books, f, indent=2)

    print(f"\n✅ Done — {len(all_books):,} books")
    print(f"   Saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
