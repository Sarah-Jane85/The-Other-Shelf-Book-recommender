"""
05_recommender_fantasy.py
─────────────────────────
TF-IDF content-based recommender for non-western fantasy books.

Loads the cleaned dataset, builds a text corpus with synonym normalization,
fits a TF-IDF vectorizer, and serializes the model for the Streamlit app.

Usage:
    python 05_recommender_fantasy.py

Output:
    Models/tfidf_matrix.npz
    Models/vectorizer.pkl
    Models/books_index.json
"""

import json
import re
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = REPO_ROOT / "Data" / "Clean"
MODEL_DIR = REPO_ROOT / "Models"
MODEL_DIR.mkdir(exist_ok=True)

# ── Constants ─────────────────────────────────────────────────────────────────
UNDERREPRESENTED = {
    "oceania", "australian-fantasy", "indigenous-fantasy", "indigenous_americas",
    "latin-american-fantasy", "latin_american", "south-american-fantasy",
    "middle-eastern-fantasy", "middle_eastern", "filipino", "southeast_asian",
    "african-science-fiction", "orisha", "igbo", "akan", "zulu", "yoruba",
    "anansi", "xianxia", "wuxia",
}

SYNONYM_MAP = {
    "mage": "magic_user", "sorcerer": "magic_user", "wizard": "magic_user",
    "enchanter": "magic_user", "warlock": "magic_user", "magician": "magic_user",
    "witch": "magic_user", "shaman": "magic_user", "spellcaster": "magic_user",
    "sorcery": "magic", "witchcraft": "magic", "enchantment": "magic",
    "spells": "magic", "arcane": "magic", "mystical": "magic",
    "fighter": "warrior", "soldier": "warrior", "knight": "warrior",
    "samurai": "warrior", "hunter": "warrior", "assassin": "warrior",
    "mercenary": "warrior",
    "queen": "royalty", "king": "royalty", "emperor": "royalty",
    "empress": "royalty", "prince": "royalty", "princess": "royalty",
    "ruler": "royalty", "throne": "royalty",
    "demon": "spirit", "god": "spirit", "goddess": "spirit",
    "deity": "spirit", "ancestor": "spirit", "ghost": "spirit",
    "orisha": "spirit",
    "quest": "journey", "adventure": "journey", "expedition": "journey",
    "travel": "journey", "mission": "journey", "voyage": "journey",
}

CUSTOM_STOP = list(ENGLISH_STOP_WORDS) + [
    "book", "novel", "fiction", "author", "story", "stories",
    "series", "readers", "bestselling", "award", "pages", "work",
    "known", "written", "writing", "writer", "read", "reading", "writers",
    "works", "collection",
    "life", "young", "people", "new", "world", "time", "old",
    "man", "woman", "girl", "boy", "father", "mother", "son",
    "daughter", "human", "way", "day", "year", "years",
    "save", "help", "come", "comes", "find", "finds",
    "take", "takes", "make", "makes", "begin", "begins", "like",
    "stop", "wants", "debut", "epic", "things", "left", "age",
    "knows", "long", "set", "just", "best",
    "na", "tan", "scott", "morgan",
    "american", "city",
]


# ── Helper functions ──────────────────────────────────────────────────────────
def clean_title(title: str) -> str:
    """Remove edition/format suffixes from book titles."""
    title = re.sub(
        r'\s*[\(\[](hardcover|paperback|kindle edition|ebook|mass market paperback|'
        r'audio cd|audiobook|unknown binding|library binding|board book|large print)[\)\]]',
        '', title, flags=re.IGNORECASE
    )
    return title.strip()


def build_text(row: pd.Series) -> str:
    """Combine description, subjects, title and author into one text field.
    Title and author are weighted x2 by repetition."""
    parts = []
    if row.get("description"):
        parts.append(str(row["description"]))
    subjects = row.get("subjects", [])
    if isinstance(subjects, list) and subjects:
        parts.append(" ".join(str(s) for s in subjects))
    parts.append(str(row.get("title", "")) * 2)
    parts.append(str(row.get("author", "")) * 2)
    return " ".join(parts).strip()


def normalize_synonyms(text: str) -> str:
    """Replace synonyms with canonical terms for better TF-IDF matching."""
    words = str(text).lower().split()
    return " ".join(SYNONYM_MAP.get(w, w) for w in words)


def recommend_three_lanes(
    query_title: str,
    df: pd.DataFrame,
    tfidf_matrix,
    top_n: int = 5
) -> dict | None:
    """Return three-lane recommendations for a given book title.

    Args:
        query_title: Partial or full title to search for.
        df: Books dataframe.
        tfidf_matrix: Fitted sparse TF-IDF matrix.
        top_n: Number of results per lane.

    Returns:
        Dict with keys: query_book, same_author, similar, hidden_gems.
        Returns None if title not found.
    """
    matches = df[df["title"].str.contains(query_title, case=False, na=False)]
    if len(matches) == 0:
        print(f"❌ '{query_title}' not found in dataset")
        return None

    idx          = matches.index[0]
    query_book   = df.iloc[idx]
    query_vec    = tfidf_matrix[idx]
    query_author = query_book["author"].lower().strip()

    sim_scores            = cosine_similarity(query_vec, tfidf_matrix).flatten()
    results               = df.copy()
    results["similarity"] = sim_scores
    results               = results.drop(index=idx)

    same_author = results[
        results["author"].str.lower().str.strip() == query_author
    ].sort_values("similarity", ascending=False).head(top_n)

    similar = results[
        results["author"].str.lower().str.strip() != query_author
    ].sort_values("similarity", ascending=False).head(top_n)

    hidden_gems_pool = results[
        (results["source_tag"].isin(UNDERREPRESENTED)) &
        (results["author"].str.lower().str.strip() != query_author) &
        (results["similarity"] >= 0.02)
    ]
    hidden_gems = (
        hidden_gems_pool
        .sort_values("similarity", ascending=False)
        .groupby("source_tag").first()
        .reset_index()
        .sort_values("similarity", ascending=False)
        .head(top_n)
    )

    return {
        "query_book":  query_book,
        "same_author": same_author,
        "similar":     similar,
        "hidden_gems": hidden_gems,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # Load data
    with open(CLEAN_DIR / "merged_non_western_fantasy.json") as f:
        df = pd.DataFrame(json.load(f))
    print(f"✅ Loaded {len(df):,} books")

    # Build text field
    df["title"] = df["title"].apply(clean_title)
    df["text"]  = df.apply(build_text, axis=1)
    df["text"]  = df["text"].apply(normalize_synonyms)
    print("✅ Text field built and synonyms normalized")

    # Save updated dataset
    df["subjects"] = df["subjects"].apply(lambda x: x if isinstance(x, list) else [])
    df.to_json(CLEAN_DIR / "merged_non_western_fantasy.json",
               orient="records", indent=2, force_ascii=False)
    print("✅ Dataset saved")

    # Fit TF-IDF
    vectorizer = TfidfVectorizer(
        max_features=5000,
        stop_words=CUSTOM_STOP,
        min_df=3,
        ngram_range=(1, 2)
    )
    tfidf_matrix = vectorizer.fit_transform(df["text"])
    print(f"✅ TF-IDF matrix: {tfidf_matrix.shape[0]:,} books × {tfidf_matrix.shape[1]:,} features")

    # Test recommender
    print("\n── Quick test ──")
    result = recommend_three_lanes("Children of Blood and Bone", df, tfidf_matrix)
    if result:
        print(f"Query: {result['query_book']['title']}")
        print(f"Top similar: {result['similar']['title'].iloc[0]}")

    # Serialize model
    sparse.save_npz(MODEL_DIR / "tfidf_matrix.npz", tfidf_matrix)
    with open(MODEL_DIR / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    df.drop(columns=["text"]).to_json(
        MODEL_DIR / "books_index.json", orient="records", indent=2, force_ascii=False
    )
    print(f"\n✅ Model serialized to {MODEL_DIR}")


if __name__ == "__main__":
    main()
