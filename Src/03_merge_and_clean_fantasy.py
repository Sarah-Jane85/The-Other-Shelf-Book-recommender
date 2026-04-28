"""
03_merge_and_clean_fantasy.py
──────────────────────────────
Merges and cleans the Open Library and Goodreads datasets into a single
unified file, with description enrichment from Google Books and OpenLibrary.

Steps:
1. Filter OL and Goodreads data (western authors, nonfiction, coloring books)
2. Normalize schemas and merge (Goodreads wins on overlaps)
3. Enrich missing descriptions via Google Books API
4. Enrich remaining missing descriptions via OpenLibrary API
5. Filter non-English books and fallback descriptions
6. Deduplicate and clean datatypes
7. Save final dataset

Usage:
    python 03_merge_and_clean_fantasy.py

Output:
    Data/Clean/merged_non_western_fantasy.json
    Data/Clean/merged_non_western_fantasy.csv
"""

import json
import os
import re
import time
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
from langdetect import detect

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT  = Path(__file__).resolve().parents[2]
RAW_DIR    = REPO_ROOT / "Data" / "Raw" / "non_western_fantasy"
CLEAN_DIR  = REPO_ROOT / "Data" / "Clean"
CLEAN_DIR.mkdir(exist_ok=True)

GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")

# ── Filter sets ───────────────────────────────────────────────────────────────
WESTERN_NOISE_AUTHORS = {
    'edgar rice burroughs', 'h. rider haggard', 'rudyard kipling',
    'joseph conrad', 'wilbur smith', 'james michener', 'john buchan',
    'arthur conan doyle', 'h.g. wells', 'h. g. wells', 'jules verne',
    'charlotte perkins gilman', 'george macdonald', 'd. h. lawrence',
    'lucy maud montgomery', 'carlo collodi', 'neil gaiman',
    'george r. r. martin', 'rick riordan', 'j. k. rowling',
    'bram stoker', 'edith nesbit', 'l. frank baum',
    'richard adams', 'roald dahl', 'c. s. lewis', 'c.s. lewis',
    'stephen king', 'astrid lindgren', 'bill willingham',
    'mary shelley', 'niccolò machiavelli', 'michael ende',
    'charles kingsley', 'andrew lang', 'dr. seuss', 'lewis carroll',
    'edgar allan poe', 'nathaniel hawthorne', 'mark twain',
    'antoine de saint-exupéry', 'christopher paolini', 'j.r.r. tolkien',
    'mercedes lackey', 'piers anthony', 'mary pope osborne',
    'daisy meadows', 'erin hunter', 'paul theroux', 'harold macgrath',
    'charles de lint', 'james rollins', 'e. b. white', 'e.b. white',
    'philip pullman', 'terry pratchett', 'margaret atwood', 'george orwell',
    'frank herbert', 'isaac asimov', 'robert jordan', 'anne mccaffrey',
    'brandon sanderson', 'sarah j. maas', 'cassandra clare', 'ray bradbury',
    'hans christian andersen', 'william shakespeare', 'franz kafka',
    'iain banks', 'arthur c. clarke', 'lois mcmaster bujold',
    'susanna clarke', 'kelly link', 'jane yolen',
    # Extra western authors found via clustering
    'stephen king', 'caroline peckham', 'neal stephenson',
    'sarah a. parker', 'samantha shannon', 'olivia blake',
    'kazuo ishiguro', 'truman capote', 'shel silverstein',
    'laura dave', 'gabrielle zevin', 'marissa meyer', 'pierce brown',
    'naomi novik', 'diana wynne jones', 'raymond e. feist',
    'lafcadio hearn', 'ruth r. carter',
}

NOISE_SUBJECTS = {'tarzan', 'colonialism', 'imperialism', 'safari', 'big game hunting', 'missionaries'}

COMIC_SUBJECTS = {'graphic novel', 'graphic novels', 'comics', 'comic book', 'comic strip', 'sequential art'}

NONFICTION_SUBJECTS = {
    'criticism', 'critical essays', 'literary criticism',
    'history and criticism', 'congresses', 'study and teaching',
    'nonfiction', 'biography', 'autobiography',
    'education', 'philosophy', 'sociology', 'political science',
    'essays', 'handbooks', 'reference',
    'cross-cultural studies', 'mass media', 'self-perception',
    'creative ability in children', 'imagination in children',
}

NONFICTION_TITLE_SIGNALS = {
    'biography', 'autobiography', 'interviews', 'conversations with',
    'art of ', 'making of', 'the life of', 'history of',
    'study guide', 'essays on', 'criticism', 'scholarly',
    'coloring book', 'colouring book', 'activity book',
}

ORG_SIGNALS = ['publishing llc', 'publishing inc', 'enterprises', 'museum',
               'institute', 'university', 'library of congress', 'disney', 'various']

TITLE_NOISE = [
    "Art of Ruth E. Carter", "Conversations with Octavia Butler",
    "Bloodchildren: Stories by the Octavia E. Butler Scholars",
    "Strange Matings: Science Fiction, Feminism, African American Voices",
    "Positive Obsession: The Life and Times of Octavia E. Butler",
    "Why Wakanda Matters", "MCU: The Reign of Marvel Studios",
    "Star Child: A Biographical Constellation", "NOT A BOOK",
    "Charlotte's Web",
]

JUNK_SIGNALS = [
    'tagebuch', 'notizbuch', 'malbuch', 'planer', 'kalender',
    'coloring', 'colouring', 'color by number', 'weight tracker',
    'expense tracker', 'password log', 'music sheet', 'genkoyoushi',
    'house sitting', 'self care', 'reading list book',
    'choreograph', 'dancing for', 'folk dance', 'cookbook', 'recipes',
    'guitar solo', 'diabetes', 'trivia', 'food fantasy fgb',
    'interview', 'biograpghical', 'marvel studios', 'marvel',
    'coloring book',
]


# ── Filter functions ──────────────────────────────────────────────────────────
def ol_filter(row: pd.Series) -> bool:
    """Return True if the OL book should be kept."""
    author        = str(row.get('author', '')).lower().strip()
    subjects_text = ' '.join(str(s) for s in (row.get('subjects') or [])).lower()
    if author in WESTERN_NOISE_AUTHORS:
        return False
    if any(n in subjects_text for n in NOISE_SUBJECTS):
        return False
    if any(c in subjects_text for c in COMIC_SUBJECTS):
        return False
    if any(n in subjects_text for n in NONFICTION_SUBJECTS):
        return False
    return True


def gr_filter(row: pd.Series) -> bool:
    """Return True if the Goodreads book should be kept."""
    author     = str(row.get('author', '')).lower().strip()
    title_text = str(row.get('title', '')).lower()
    if author in WESTERN_NOISE_AUTHORS:
        return False
    if any(n in title_text for n in NONFICTION_TITLE_SIGNALS):
        return False
    return True


def is_junk(row: pd.Series) -> bool:
    """Return True if the book is junk (no description, no ratings, noise title)."""
    has_desc    = bool(str(row.get('description', '')).strip()) and \
                  str(row.get('description', '')).strip() != 'nan'
    has_ratings = pd.notna(row.get('num_ratings')) and row.get('num_ratings', 0) > 0
    if has_desc or has_ratings:
        return False
    return any(s in str(row.get('title', '')).lower() for s in JUNK_SIGNALS)


def is_english(text: str) -> bool:
    """Return True if the text is detected as English."""
    try:
        return detect(str(text)) == 'en'
    except Exception:
        return False


def has_english_title(title: str) -> bool:
    """Return True if the title is detected as English."""
    try:
        return detect(str(title)) == 'en'
    except Exception:
        return True


def norm_title(t: str) -> str:
    t = str(t).lower().strip()
    t = re.sub(r'\s*[\(\[].*?[\)\]]\s*', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def norm_author(a: str) -> str:
    return str(a).lower().strip()


def clean_title(title: str) -> str:
    title = re.sub(
        r'\s*[\(\[](hardcover|paperback|kindle edition|ebook|mass market paperback|'
        r'audio cd|audiobook|unknown binding|library binding|board book|large print)[\)\]]',
        '', title, flags=re.IGNORECASE
    )
    return title.strip()


# ── Description enrichment ────────────────────────────────────────────────────
def fetch_google_books_description(title: str, author: str = "") -> dict | None:
    """Fetch an English description from Google Books API."""
    if not GOOGLE_BOOKS_API_KEY:
        return None
    params = {
        'q':          f'{title} {author}'.strip(),
        'maxResults': 5,
        'key':        GOOGLE_BOOKS_API_KEY,
        'fields':     'items(volumeInfo(title,authors,description,publishedDate,imageLinks))'
    }
    try:
        resp = requests.get('https://www.googleapis.com/books/v1/volumes',
                            params=params, timeout=10)
        resp.raise_for_status()
        for item in resp.json().get('items', []):
            info = item.get('volumeInfo', {})
            desc = info.get('description', '')
            if desc:
                try:
                    if detect(desc) == 'en':
                        return {
                            'description': desc,
                            'cover_url':   info.get('imageLinks', {}).get('thumbnail', ''),
                        }
                except Exception:
                    continue
        return None
    except Exception:
        return None


def fetch_ol_description(ol_url: str) -> str | None:
    """Fetch description from OpenLibrary works API."""
    key = ol_url.replace('https://openlibrary.org', '')
    if not key.startswith('/works/'):
        return None
    try:
        r    = requests.get(f'https://openlibrary.org{key}.json', timeout=10)
        desc = r.json().get('description', '')
        if isinstance(desc, dict):
            desc = desc.get('value', '')
        return str(desc).strip() if desc and len(str(desc).strip()) > 20 else None
    except Exception:
        return None


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # ── Load raw data ─────────────────────────────────────────────────────────
    ol_raw = pd.DataFrame(json.load(open(RAW_DIR / 'ol_genre_first.json')))
    gr_raw = pd.read_csv(RAW_DIR / 'goodreads_with_descriptions.csv')
    print(f"✅ Loaded — OL: {len(ol_raw):,} | Goodreads: {len(gr_raw):,}")

    # ── Filter both sources ───────────────────────────────────────────────────
    ol_clean = ol_raw[ol_raw.apply(ol_filter, axis=1)].copy().reset_index(drop=True)
    ol_clean = ol_clean[ol_clean['author'].str.strip() != ''].reset_index(drop=True)
    gr_clean = gr_raw[gr_raw.apply(gr_filter, axis=1)].copy().reset_index(drop=True)
    print(f"After filtering — OL: {len(ol_clean):,} | Goodreads: {len(gr_clean):,}")

    # ── Normalize schemas ─────────────────────────────────────────────────────
    ol_unified = pd.DataFrame({
        'title':          ol_clean['title'].str.strip(),
        'author':         ol_clean['author'].fillna(''),
        'description':    ol_clean['description'].fillna(''),
        'year_published': ol_clean['year_published'],
        'cover_url':      ol_clean['cover_url'].fillna(''),
        'avg_rating':     ol_clean['avg_rating'],
        'num_ratings':    ol_clean['num_ratings'],
        'subjects':       ol_clean['subjects'].apply(lambda x: x if isinstance(x, list) else []),
        'source':         'open_library',
        'source_url':     ol_clean['source_url'],
        'source_tag':     ol_clean['source_tag'],
        'title_norm':     ol_clean['title'].apply(norm_title),
        'author_norm':    ol_clean['author'].fillna('').apply(norm_author),
    })

    gr_unified = pd.DataFrame({
        'title':          gr_clean['title'].str.strip(),
        'author':         gr_clean['author'].fillna(''),
        'description':    gr_clean['description'].fillna(''),
        'year_published': gr_clean['year_published'],
        'cover_url':      gr_clean['cover_url'].fillna(''),
        'avg_rating':     gr_clean['avg_rating'],
        'num_ratings':    gr_clean['num_ratings'],
        'subjects':       [[] for _ in range(len(gr_clean))],
        'source':         'goodreads',
        'source_url':     gr_clean['goodreads_url'],
        'source_tag':     gr_clean['shelf'],
        'title_norm':     gr_clean['title'].apply(norm_title),
        'author_norm':    gr_clean['author'].fillna('').apply(norm_author),
    })

    # ── Merge (Goodreads wins on overlap) ─────────────────────────────────────
    gr_lookup = {(r['title_norm'], r['author_norm']): r
                 for _, r in gr_unified.iterrows()}

    enriched_ol = []
    for _, row in ol_unified.iterrows():
        key      = (row['title_norm'], row['author_norm'])
        gr_match = gr_lookup.get(key)
        if gr_match is not None:
            row = row.copy()
            if gr_match['description']:    row['description']    = gr_match['description']
            if gr_match['cover_url']:      row['cover_url']      = gr_match['cover_url']
            if pd.notna(gr_match['avg_rating']): row['avg_rating'] = gr_match['avg_rating']
            if pd.notna(gr_match['num_ratings']): row['num_ratings'] = gr_match['num_ratings']
        enriched_ol.append(row)

    ol_enriched = pd.DataFrame(enriched_ol)
    gr_keys     = set(gr_lookup.keys())
    ol_only     = ol_enriched[~ol_enriched.apply(
        lambda r: (r['title_norm'], r['author_norm']) in gr_keys, axis=1
    )]
    merged = pd.concat([gr_unified, ol_only], ignore_index=True)
    merged = merged.drop(columns=['title_norm', 'author_norm'])
    print(f"After merge: {len(merged):,} books")

    # ── Google Books description enrichment ───────────────────────────────────
    GB_CKPT = CLEAN_DIR / 'google_books_checkpoint.json'
    gb_results = json.load(open(GB_CKPT)) if GB_CKPT.exists() else {}
    needs_desc = merged[merged['description'].apply(
        lambda x: not bool(str(x).strip()) or str(x).strip() == 'nan'
    )]
    remaining = needs_desc[~needs_desc['source_url'].isin(gb_results.keys())]
    print(f"Google Books: {len(gb_results):,} done | {len(remaining):,} remaining")

    stats = {'filled': 0, 'not_found': 0}
    for i, (idx, row) in enumerate(tqdm(remaining.iterrows(), total=len(remaining)), 1):
        result = fetch_google_books_description(row['title'], row['author'])
        gb_results[row['source_url']] = result if result else {}
        stats['filled' if result else 'not_found'] += 1
        if i % 100 == 0:
            json.dump(gb_results, open(GB_CKPT, 'w'))
        time.sleep(0.5)

    json.dump(gb_results, open(GB_CKPT, 'w'))
    for idx, row in merged.iterrows():
        gb = gb_results.get(row['source_url'], {})
        if gb.get('description') and not bool(str(row['description']).strip()):
            merged.at[idx, 'description'] = gb['description']
        if gb.get('cover_url') and not bool(str(row['cover_url']).strip()):
            merged.at[idx, 'cover_url'] = gb['cover_url']
    print(f"Google Books filled: {stats['filled']:,} | not found: {stats['not_found']:,}")

    # ── OpenLibrary description enrichment ───────────────────────────────────
    OL_CKPT = CLEAN_DIR / 'ol_desc_checkpoint.json'
    ol_desc_results = json.load(open(OL_CKPT)) if OL_CKPT.exists() else {}
    still_missing = merged[
        merged['description'].apply(lambda x: not bool(str(x).strip()) or str(x).strip() == 'nan') &
        (merged['source'] == 'open_library')
    ]
    remaining_ol = still_missing[~still_missing['source_url'].isin(ol_desc_results.keys())]

    for i, (idx, row) in enumerate(tqdm(remaining_ol.iterrows(), total=len(remaining_ol)), 1):
        result = fetch_ol_description(row['source_url'])
        ol_desc_results[row['source_url']] = result or ''
        if i % 100 == 0:
            json.dump(ol_desc_results, open(OL_CKPT, 'w'))
        time.sleep(0.3)

    json.dump(ol_desc_results, open(OL_CKPT, 'w'))
    for idx, row in merged.iterrows():
        desc = ol_desc_results.get(row['source_url'], '')
        if desc and not bool(str(row['description']).strip()):
            merged.at[idx, 'description'] = desc

    # ── Remove junk books ─────────────────────────────────────────────────────
    merged = merged[~merged.apply(is_junk, axis=1)].copy().reset_index(drop=True)

    # Subjects fallback for remaining missing descriptions
    for idx, row in merged.iterrows():
        if bool(str(row['description']).strip()) and str(row['description']).strip() != 'nan':
            continue
        subj = [str(s).strip() for s in (row['subjects'] if isinstance(row['subjects'], list) else [])
                if len(str(s).strip()) > 2][:10]
        if subj:
            merged.at[idx, 'description'] = 'A work of fantasy fiction involving: ' + ', '.join(subj) + '.'

    # ── Additional filters ────────────────────────────────────────────────────
    merged = merged[~merged['title'].isin(TITLE_NOISE)].reset_index(drop=True)
    merged = merged[~merged['title'].str.contains('coloring book', case=False, na=False)].reset_index(drop=True)
    merged = merged[~merged['author'].str.lower().str.strip().apply(
        lambda a: any(s in a for s in ORG_SIGNALS)
    )].reset_index(drop=True)

    # Filter non-English books with only fallback descriptions
    fallback_mask = merged['description'].str.contains('A work of fantasy fiction involving', na=False)
    non_english_title = ~merged['title'].apply(has_english_title)
    merged = merged[~(fallback_mask & non_english_title)].reset_index(drop=True)

    # English-only descriptions
    merged = merged[merged['description'].apply(is_english)].reset_index(drop=True)
    print(f"After language filter: {len(merged):,}")

    # ── Dedup + datatype cleanup ──────────────────────────────────────────────
    merged['title'] = merged['title'].apply(clean_title)
    before = len(merged)
    merged['_title_norm']  = merged['title'].str.lower().str.strip()
    merged['_author_norm'] = merged['author'].str.lower().str.strip()
    merged['_source_rank'] = merged['source'].map({'goodreads': 0, 'open_library': 1})
    merged = (merged
              .sort_values('_source_rank')
              .drop_duplicates(subset=['_title_norm', '_author_norm'], keep='first')
              .drop(columns=['_title_norm', '_author_norm', '_source_rank'])
              .reset_index(drop=True))
    print(f"Duplicates removed: {before - len(merged):,}")

    merged['year_published'] = pd.to_numeric(merged['year_published'], errors='coerce').fillna(0).astype(int).replace(0, None)
    merged['num_ratings']    = pd.to_numeric(merged['num_ratings'], errors='coerce').fillna(0).astype(int)
    merged['avg_rating']     = merged['avg_rating'].round(2)
    merged['subjects']       = merged['subjects'].apply(lambda x: x if isinstance(x, list) else [])
    for col in ['title', 'author', 'description', 'cover_url', 'source_url', 'source_tag']:
        merged[col] = merged[col].str.strip()

    # ── Save ──────────────────────────────────────────────────────────────────
    FINAL_PATH = CLEAN_DIR / 'merged_non_western_fantasy.json'
    merged.to_json(FINAL_PATH, orient='records', indent=2, force_ascii=False)
    merged.to_csv(CLEAN_DIR / 'merged_non_western_fantasy.csv', index=False)

    print(f"\n✅ Pipeline complete!")
    print(f"   Total books: {len(merged):,}")
    print(f"   Saved to:    {FINAL_PATH}")


if __name__ == "__main__":
    main()
