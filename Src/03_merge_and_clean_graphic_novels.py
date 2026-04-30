"""
03 Merge and Clean — Graphic Novels

Goal:
Clean and filter the graphic novel dataset.

Run from the project root:
    python Src/03_merge_and_clean_graphic_novels.py

Input:
    Data/Clean/graphic_novels_with_descriptions.csv

Output:
    Data/Clean/merged_graphic_novels.csv
"""

from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "Data" / "Clean" / "graphic_novels_with_descriptions.csv"
OUTPUT_PATH = ROOT / "Data" / "Clean" / "merged_graphic_novels.csv"

COLUMNS_TO_KEEP = [
    "title",
    "author",
    "first_publish_year",
    "publisher",
    "language",
    "subject",
    "isbn",
    "cover_i",
    "description",
    "search_term",
    "ol_key",
]

INCLUDE_TERMS = [
    "graphic novel",
    "graphic novels",
    "sequential art",
    "graphic memoir",
    "illustrated",
    "cartoon",
    "visual storytelling",
]

EXCLUDE_TERMS = [
    # educational / instructional
    "how to",
    "guide",
    "manual",
    "workbook",
    "textbook",
    "lesson",
    "curriculum",
    "course",
    "introduction to",
    "study of",
    # making comics
    "write your own",
    "how to draw",
    "drawing",
    "learn to draw",
    "making comics",
    "create comics",
    "comic creation",
    # theory / analysis
    "history of comics",
    "theory",
    "analysis",
    "criticism",
    "review",
    "essays on",
    "understanding comics",
    "inventing comics",
    # professions
    "animation",
    "working in animation",
    # general noise
    "coloring book",
    "activity book",
    "children's",
    "children",
    "teacher",
    "students",
]

NARRATIVE_KEYWORDS = [
    "story",
    "tale",
    "novel",
    "memoir",
    "journey",
    "life",
    "family",
    "war",
    "history",
    "love",
    "childhood",
    "coming of age",
]


def clean_text(text) -> str:
    """Basic text cleaning for descriptions and subjects."""
    if pd.isna(text):
        return ""

    text = str(text).lower()
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_regex(terms: list[str]) -> str:
    """Escape terms before joining them into a regex pattern."""
    return "|".join(re.escape(term) for term in terms)


def main() -> None:
    df = pd.read_csv(INPUT_PATH)
    print(f"Loaded rows: {len(df):,}")

    df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")
    df = df[[col for col in COLUMNS_TO_KEEP if col in df.columns]]

    df = df.dropna(subset=["title", "author", "description"])
    df = df.drop_duplicates(subset=["title", "author"])
    print(f"Rows after required fields + dedupe: {len(df):,}")

    # Clean text BEFORE narrative filtering so the full script runs top-to-bottom.
    df["clean_description"] = df["description"].apply(clean_text)
    df["clean_subject"] = df["subject"].apply(clean_text) if "subject" in df.columns else ""

    df["filter_text"] = (
        df["title"].fillna("")
        + " "
        + df["author"].fillna("")
        + " "
        + df.get("subject", pd.Series("", index=df.index)).fillna("")
        + " "
        + df["description"].fillna("")
    ).str.lower()

    include_pattern = build_regex(INCLUDE_TERMS)
    exclude_pattern = build_regex(EXCLUDE_TERMS)

    df = df[df["filter_text"].str.contains(include_pattern, na=False, regex=True)]
    df = df[~df["filter_text"].str.contains(exclude_pattern, na=False, regex=True)]
    print(f"Rows after include/exclude filters: {len(df):,}")

    df = df[df["clean_description"].apply(lambda x: any(k in x for k in NARRATIVE_KEYWORDS))]
    print(f"Rows after narrative filter: {len(df):,}")

    df["combined_text"] = (
        df["title"].fillna("")
        + " "
        + df["author"].fillna("")
        + " "
        + df["clean_subject"].fillna("")
        + " "
        + df["clean_description"].fillna("")
    )

    df["cover_url"] = df["cover_i"].apply(
        lambda x: f"https://covers.openlibrary.org/b/id/{int(x)}-M.jpg" if pd.notna(x) else None
    )

    # Keep filter_text available for debugging? Drop it for cleaner output.
    df = df.drop(columns=["filter_text"], errors="ignore")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Saved clean data to: {OUTPUT_PATH}")
    print(f"Final rows: {len(df):,}")

    # Quick sanity checks for key authors.
    for author in ["satrapi", "eisner", "spiegelman"]:
        matches = df[df["author"].str.contains(author, case=False, na=False)]
        print(f"{author.title()} matches: {len(matches)}")


if __name__ == "__main__":
    main()
