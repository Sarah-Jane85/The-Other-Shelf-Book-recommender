"""
04 EDA — Graphic Novels

Goal:
Explore the cleaned graphic novel dataset and create visuals for the final report.

Run from the project root:
    python Src/04_eda_graphic_novels.py

Input:
    Data/Clean/merged_graphic_novels.csv

Outputs:
    Reports/EDA_Graphic_Novels/*.png
"""

from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "Data" / "Clean" / "merged_graphic_novels.csv"
REPORT_DIR = ROOT / "Reports" / "EDA_Graphic_Novels"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)
    print(f"Loaded clean rows: {len(df):,}")
    print(df.info())
    print("\nMissing values:")
    print(df.isna().sum())

    # Publication years.
    years = df["first_publish_year"].dropna()
    plt.figure(figsize=(10, 5))
    plt.hist(years, bins=30)
    plt.title("Publication Year Distribution — Graphic Novels")
    plt.xlabel("First Publish Year")
    plt.ylabel("Number of Books")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "01_publication_years.png")
    plt.close()

    # Top authors.
    top_authors = df["author"].value_counts().head(15)
    plt.figure(figsize=(10, 6))
    top_authors.sort_values().plot(kind="barh")
    plt.title("Top Authors in Graphic Novel Dataset")
    plt.xlabel("Number of Books")
    plt.ylabel("Author")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "02_top_authors.png")
    plt.close()

    # Common words in descriptions.
    all_text = " ".join(df["clean_description"].dropna())
    words = all_text.split()
    stopwords = {
        "the", "and", "of", "to", "a", "in", "is", "for", "with", "on", "as",
        "by", "an", "from", "this", "that", "it", "be", "are", "at", "or",
        "his", "her", "their", "its", "into", "about", "new", "one", "book",
    }
    filtered_words = [word for word in words if word not in stopwords and len(word) > 3]
    word_counts = Counter(filtered_words).most_common(20)
    words_df = pd.DataFrame(word_counts, columns=["word", "count"])

    plt.figure(figsize=(10, 6))
    plt.barh(words_df["word"], words_df["count"])
    plt.title("Most Common Words in Graphic Novel Descriptions")
    plt.xlabel("Count")
    plt.ylabel("Word")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "03_description_words.png")
    plt.close()

    # Theme keyword counts.
    theme_keywords = {
        "memoir": "memoir",
        "history": "history",
        "war": "war",
        "family": "family",
        "identity": "identity",
        "politics": "politic",
        "love": "love",
        "death": "death",
        "art": "art",
        "life": "life",
    }

    theme_counts = {}
    for theme, keyword in theme_keywords.items():
        theme_counts[theme] = df["combined_text"].str.contains(keyword, case=False, na=False).sum()

    theme_df = pd.DataFrame(list(theme_counts.items()), columns=["theme", "count"]).sort_values(
        "count", ascending=True
    )

    plt.figure(figsize=(10, 6))
    plt.barh(theme_df["theme"], theme_df["count"])
    plt.title("Recurring Themes in Graphic Novel Dataset")
    plt.xlabel("Number of Books")
    plt.ylabel("Theme")
    plt.tight_layout()
    plt.savefig(REPORT_DIR / "04_theme_counts.png")
    plt.close()

    summary = {
        "total_books": len(df),
        "unique_authors": df["author"].nunique(),
        "earliest_year": df["first_publish_year"].min(),
        "latest_year": df["first_publish_year"].max(),
        "books_with_cover": df["cover_url"].notna().sum(),
    }
    print("\nEDA summary:")
    print(summary)
    print(f"\nSaved charts to: {REPORT_DIR}")


if __name__ == "__main__":
    main()
