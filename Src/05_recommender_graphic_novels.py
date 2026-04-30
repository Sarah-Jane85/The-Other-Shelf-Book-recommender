"""
05 Recommender — Graphic Novels

Goal:
Build a content-based recommendation system using TF-IDF and cosine similarity.

Run from the project root:
    python Src/05_recommender_graphic_novels.py

Input:
    Data/Clean/merged_graphic_novels.csv

Outputs:
    Models/graphic_vectorizer.pkl
    Models/graphic_tfidf_matrix.npz
    Models/graphic_books_index.json
"""

from pathlib import Path
import json
import pickle

import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "Data" / "Clean" / "merged_graphic_novels.csv"
MODELS_DIR = ROOT / "Models"


def recommend_books(title: str, df: pd.DataFrame, tfidf_matrix, top_n: int = 5) -> pd.DataFrame:
    """Return top_n recommendations for a title query."""
    title = title.lower()
    matches = df[df["title"].str.lower().str.contains(title, na=False)]

    if matches.empty:
        return pd.DataFrame(columns=["title", "author", "description", "cover_url"])

    idx = matches.index[0]
    cosine_scores = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
    similar_indices = cosine_scores.argsort()[::-1][1 : top_n + 1]

    recommendations = df.iloc[similar_indices][
        ["title", "author", "first_publish_year", "description", "cover_url"]
    ].copy()
    recommendations["similarity_score"] = cosine_scores[similar_indices]
    return recommendations


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)
    print(f"Loaded rows: {len(df):,}")

    for col in ["clean_description", "title", "author"]:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("")

    # Repeat clean_description to weight the story/description more heavily than metadata.
    df["combined_text"] = (
        df["clean_description"]
        + " "
        + df["clean_description"]
        + " "
        + df["title"]
        + " "
        + df["author"]
    )

    vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
    tfidf_matrix = vectorizer.fit_transform(df["combined_text"])
    print(f"TF-IDF matrix shape: {tfidf_matrix.shape}")

    # Optional sanity test if the title exists.
    test_query = "maus"
    test_recs = recommend_books(test_query, df, tfidf_matrix, top_n=5)
    if not test_recs.empty:
        print(f"\nSample recommendations for '{test_query}':")
        print(test_recs[["title", "author", "similarity_score"]].to_string(index=False))
    else:
        print(f"\nNo sample recommendations found for '{test_query}'.")

    with open(MODELS_DIR / "graphic_vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)

    sparse.save_npz(MODELS_DIR / "graphic_tfidf_matrix.npz", tfidf_matrix)

    books_index = df[
        ["title", "author", "first_publish_year", "description", "cover_url", "combined_text"]
    ].to_dict(orient="records")

    with open(MODELS_DIR / "graphic_books_index.json", "w", encoding="utf-8") as f:
        json.dump(books_index, f, ensure_ascii=False, indent=2)

    df.to_csv(INPUT_PATH, index=False)

    print("\nGraphic novels recommender files saved:")
    print(f"- {MODELS_DIR / 'graphic_vectorizer.pkl'}")
    print(f"- {MODELS_DIR / 'graphic_tfidf_matrix.npz'}")
    print(f"- {MODELS_DIR / 'graphic_books_index.json'}")


if __name__ == "__main__":
    main()
