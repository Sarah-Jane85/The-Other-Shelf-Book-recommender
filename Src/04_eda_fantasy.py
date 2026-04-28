"""
04_eda_fantasy.py
──────────────────
Exploratory Data Analysis for the non-western fantasy book dataset.

Generates 13 charts saved to Reports/EDA-Fantasy/:
    01 - Books by region
    02 - Publication year distribution
    03 - Rating distribution & popularity tiers
    04 - Top 20 most represented authors
    05 - Top 15 most rated books
    06 - Dataset coverage (source, descriptions, ratings)
    07 - Average rating by region
    08 - Top 25 source tags
    09 - Top 30 TF-IDF words across all books
    10 - Top 10 distinctive words per heritage region
    11 - Word cloud of dominant themes
    12a - HDBSCAN clustering scatter plot
    12b - Heritage regions scatter plot (UMAP)
    13 - Synonym group analysis

Usage:
    python 04_eda_fantasy.py

Requirements:
    uv pip install wordcloud umap-learn hdbscan
"""

import json
import subprocess
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS

# Install optional dependencies
subprocess.run(["uv", "pip", "install", "wordcloud", "umap-learn", "hdbscan"], check=True)
from wordcloud import WordCloud
import umap
import hdbscan

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parents[2]
CLEAN_DIR   = REPO_ROOT / "Data" / "Clean"
REPORTS_DIR = REPO_ROOT / "Reports" / "EDA-Fantasy"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams["figure.dpi"] = 120

# ── Region map ────────────────────────────────────────────────────────────────
REGION_MAP = {
    "asian-fantasy": "Asia", "japanese": "Asia", "chinese": "Asia",
    "korean": "Asia", "wuxia": "Asia", "xianxia": "Asia",
    "southeast_asian": "Asia", "filipino": "Asia", "asian-science-fiction": "Asia",
    "afrofuturism": "Africa & Diaspora", "africa": "Africa & Diaspora",
    "african-fantasy": "Africa & Diaspora", "african-science-fiction": "Africa & Diaspora",
    "anansi": "Africa & Diaspora", "orisha": "Africa & Diaspora",
    "igbo": "Africa & Diaspora", "zulu": "Africa & Diaspora",
    "akan": "Africa & Diaspora", "yoruba": "Africa & Diaspora",
    "south_asian": "South Asia", "middle_eastern": "Middle East",
    "middle-eastern-fantasy": "Middle East", "latin_american": "Latin America",
    "latin-american-fantasy": "Latin America", "south-american-fantasy": "Latin America",
    "indigenous_americas": "Indigenous", "indigenous-fantasy": "Indigenous",
    "oceania": "Oceania", "australian-fantasy": "Oceania",
}

# ── Synonym map ───────────────────────────────────────────────────────────────
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
    "deity": "spirit", "ancestor": "spirit", "ghost": "spirit", "orisha": "spirit",
    "quest": "journey", "adventure": "journey", "expedition": "journey",
    "travel": "journey", "mission": "journey", "voyage": "journey",
}

CUSTOM_STOP = list(ENGLISH_STOP_WORDS) + [
    "book", "novel", "fiction", "author", "story", "stories",
    "series", "readers", "bestselling", "award", "pages", "work",
    "known", "written", "writing", "writer", "read", "reading", "writers",
    "works", "collection", "life", "young", "people", "new", "world", "time", "old",
    "man", "woman", "girl", "boy", "father", "mother", "son", "daughter", "human",
    "way", "day", "year", "years", "save", "help", "come", "comes", "find", "finds",
    "take", "takes", "make", "makes", "begin", "begins", "like",
    "stop", "wants", "debut", "epic", "things", "left", "age",
    "knows", "long", "set", "just", "best",
    "na", "tan", "scott", "morgan", "american", "city",
]

SYNONYM_GROUPS = {
    "Magic user":    ["mage", "sorcerer", "wizard", "enchanter", "warlock",
                      "magician", "witch", "shaman", "spellcaster"],
    "Magic":         ["magic", "magical", "sorcery", "witchcraft", "enchantment",
                      "spells", "arcane", "mystical"],
    "Warrior":       ["warrior", "fighter", "soldier", "knight", "samurai",
                      "hunter", "assassin", "mercenary"],
    "Royalty":       ["king", "queen", "emperor", "empress", "prince",
                      "princess", "ruler", "throne"],
    "Spirit/Divine": ["spirit", "demon", "god", "goddess", "deity",
                      "ancestor", "ghost", "orisha"],
    "Journey":       ["journey", "quest", "adventure", "expedition",
                      "travel", "mission", "voyage"],
}


def normalize_synonyms(text: str) -> str:
    words = str(text).lower().split()
    return " ".join(SYNONYM_MAP.get(w, w) for w in words)


# ── Load data ─────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    with open(CLEAN_DIR / "merged_non_western_fantasy.json") as f:
        df = pd.DataFrame(json.load(f))
    df["region"] = df["source_tag"].map(REGION_MAP).fillna("Other")
    print(f"✅ Loaded {len(df):,} books")
    return df


# ── Charts 1–8: Dataset overview ─────────────────────────────────────────────
def chart_01_books_by_region(df):
    region_counts = df["region"].value_counts()
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(region_counts.index, region_counts.values,
                   color=sns.color_palette("muted", len(region_counts)))
    ax.bar_label(bars, padding=4, fontsize=10)
    ax.set_xlabel("Number of Books")
    ax.set_title("Books by Region", fontsize=14, fontweight="bold")
    ax.set_xlim(0, region_counts.max() * 1.12)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "01_books_by_region.png")
    plt.close()
    print("✅ Chart 1 saved")


def chart_02_publication_years(df):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    year_all = df[(df["year_published"] >= 1950) & (df["year_published"] <= 2025)]
    counts_all = year_all["year_published"].value_counts().sort_index()
    ax1.bar(counts_all.index, counts_all.values,
            color=sns.color_palette("muted")[0], edgecolor="white", width=0.8)
    ax1.axvline(x=2000, color="red", linestyle="--", alpha=0.5, label="Year 2000")
    ax1.set_xticks(range(1950, 2026, 5))
    ax1.set_xticklabels(range(1950, 2026, 5), rotation=45, ha="right")
    ax1.set_ylabel("Number of Books")
    ax1.set_title("All Years (1950–2025)", fontsize=12, fontweight="bold")
    ax1.legend()
    year_recent = df[(df["year_published"] >= 2000) & (df["year_published"] <= 2025)]
    counts_recent = year_recent["year_published"].value_counts().sort_index()
    counts_recent.index = counts_recent.index.astype(int)
    bars = ax2.bar(counts_recent.index, counts_recent.values,
                   color=sns.color_palette("muted")[2], edgecolor="white", width=0.8)
    ax2.bar_label(bars, padding=3, fontsize=8)
    ax2.set_xticks(counts_recent.index)
    ax2.set_xticklabels(counts_recent.index.astype(int), rotation=45, ha="right")
    ax2.set_ylabel("Number of Books")
    ax2.set_title("Recent Books (2000–2025)", fontsize=12, fontweight="bold")
    fig.suptitle("Publication Year Distribution", fontsize=14, fontweight="bold", y=1.01)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "02_publication_years.png", bbox_inches="tight")
    plt.close()
    print("✅ Chart 2 saved")


def chart_03_ratings(df):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    rated = df[df["avg_rating"] > 0].copy()
    ax1.hist(rated["avg_rating"], bins=30,
             color=sns.color_palette("muted")[1], edgecolor="white")
    ax1.set_xlabel("Average Rating")
    ax1.set_ylabel("Number of Books")
    ax1.set_title("Distribution of Average Ratings", fontsize=12, fontweight="bold")
    ax1.axvline(rated["avg_rating"].mean(), color="red", linestyle="--",
                label=f"Mean: {rated['avg_rating'].mean():.2f}")
    ax1.legend()
    has_ratings = df[df["num_ratings"] > 0].copy()
    tiers = {
        "Unknown\n(0 ratings)":   (df["num_ratings"] == 0).sum(),
        "Hidden gem\n(1–100)":    ((has_ratings["num_ratings"] >= 1) & (has_ratings["num_ratings"] <= 100)).sum(),
        "Niche\n(101–1K)":        ((has_ratings["num_ratings"] > 100) & (has_ratings["num_ratings"] <= 1000)).sum(),
        "Known\n(1K–10K)":        ((has_ratings["num_ratings"] > 1000) & (has_ratings["num_ratings"] <= 10000)).sum(),
        "Popular\n(10K–100K)":    ((has_ratings["num_ratings"] > 10000) & (has_ratings["num_ratings"] <= 100000)).sum(),
        "Bestseller\n(100K+)":    (has_ratings["num_ratings"] > 100000).sum(),
    }
    bars = ax2.bar(tiers.keys(), tiers.values(),
                   color=sns.color_palette("muted", len(tiers)), edgecolor="white")
    ax2.bar_label(bars, padding=4, fontsize=10)
    ax2.set_ylabel("Number of Books")
    ax2.set_title("Popularity Tiers", fontsize=12, fontweight="bold")
    ax2.set_ylim(0, max(tiers.values()) * 1.15)
    plt.suptitle("Rating Analysis", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "03_ratings.png", bbox_inches="tight")
    plt.close()
    print("✅ Chart 3 saved")


def chart_04_top_authors(df):
    top_authors = df["author"].value_counts().head(20)
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(top_authors.index[::-1], top_authors.values[::-1],
                   color=sns.color_palette("muted")[0], edgecolor="white")
    ax.bar_label(bars, padding=4, fontsize=9)
    ax.set_xlabel("Number of Books")
    ax.set_title("Top 20 Most Represented Authors", fontsize=14, fontweight="bold")
    ax.set_xlim(0, top_authors.max() * 1.12)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "04_top_authors.png")
    plt.close()
    print("✅ Chart 4 saved")


def chart_05_most_rated(df):
    top_rated = df[df["num_ratings"] > 0].nlargest(15, "num_ratings")
    labels    = top_rated["title"].str[:35] + "\n— " + top_rated["author"]
    fig, ax   = plt.subplots(figsize=(13, 9))
    bars = ax.barh(labels.values[::-1], top_rated["num_ratings"].values[::-1],
                   color=sns.color_palette("muted")[2], edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:,}" for v in top_rated["num_ratings"].values[::-1]],
                 padding=4, fontsize=9)
    ax.set_xlabel("Number of Ratings")
    ax.set_title("Top 15 Most Rated Books in Dataset", fontsize=14, fontweight="bold")
    ax.set_xlim(0, top_rated["num_ratings"].max() * 1.25)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "05_most_rated.png")
    plt.close()
    print("✅ Chart 5 saved")


def chart_06_coverage(df):
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    source_counts = df["source"].value_counts()
    axes[0].pie(source_counts.values, labels=source_counts.index,
                autopct='%1.1f%%', colors=sns.color_palette("muted", 2))
    axes[0].set_title("Books by Source", fontweight="bold")
    has_real = df["description"].apply(
        lambda x: bool(str(x).strip()) and str(x).strip() != "nan" and
        "A work of fantasy fiction involving" not in str(x)
    ).sum()
    has_fallback = df["description"].apply(
        lambda x: "A work of fantasy fiction involving" in str(x)
    ).sum()
    has_none = len(df) - has_real - has_fallback
    axes[1].pie([has_real, has_fallback, has_none],
                labels=["Real description", "Subjects fallback", "None"],
                autopct='%1.1f%%', colors=sns.color_palette("muted", 3))
    axes[1].set_title("Description Coverage", fontweight="bold")
    has_rating = (df["num_ratings"] > 0).sum()
    no_rating  = (df["num_ratings"] == 0).sum()
    axes[2].pie([has_rating, no_rating], labels=["Has ratings", "No ratings"],
                autopct='%1.1f%%', colors=sns.color_palette("muted", 2))
    axes[2].set_title("Rating Coverage", fontweight="bold")
    plt.suptitle("Dataset Coverage Overview", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "06_coverage.png")
    plt.close()
    print("✅ Chart 6 saved")


def chart_07_rating_by_region(df):
    rated_df     = df[df["avg_rating"] > 0]
    region_stats = (rated_df.groupby("region")["avg_rating"]
                    .agg(avg_rating="mean", count="count")
                    .sort_values("avg_rating", ascending=False))
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(region_stats.index, region_stats["avg_rating"],
                   color=sns.color_palette("muted")[0], edgecolor="white")
    ax.bar_label(bars, labels=[f"{v:.2f} ({region_stats['count'][i]:,} books)"
                                for i, v in zip(region_stats.index, region_stats["avg_rating"])],
                 padding=4, fontsize=9)
    ax.set_xlabel("Average Rating")
    ax.set_title("Average Rating by Region", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 5.2)
    ax.axvline(x=rated_df["avg_rating"].mean(), color="red", linestyle="--",
               alpha=0.5, label=f"Overall mean: {rated_df['avg_rating'].mean():.2f}")
    ax.legend()
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "07_rating_by_region.png")
    plt.close()
    print("✅ Chart 7 saved")


def chart_08_top_tags(df):
    tag_counts = df["source_tag"].value_counts().head(25)
    fig, ax    = plt.subplots(figsize=(12, 8))
    bars = ax.barh(tag_counts.index[::-1], tag_counts.values[::-1], color="#7CB99A")
    ax.set_title("Top 25 Source Tags", fontsize=14, fontweight="bold")
    ax.set_xlabel("Number of Books")
    for bar, val in zip(bars, tag_counts.values[::-1]):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "08_top_tags.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Chart 8 saved")


# ── TF-IDF setup ──────────────────────────────────────────────────────────────
def build_tfidf(df):
    desc_mask = df["description"].apply(
        lambda x: bool(str(x).strip()) and str(x).strip() != "nan" and
        "A work of fantasy fiction involving" not in str(x)
    )
    df_tfidf = df[desc_mask].copy().reset_index(drop=True)
    df_tfidf["description"] = df_tfidf["description"].apply(normalize_synonyms)
    df_tfidf["region"]      = df_tfidf["source_tag"].map(REGION_MAP).fillna("Other")

    vectorizer = TfidfVectorizer(max_features=5000, stop_words=CUSTOM_STOP,
                                 min_df=3, ngram_range=(1, 2))
    tfidf_matrix  = vectorizer.fit_transform(df_tfidf["description"])
    feature_names = np.array(vectorizer.get_feature_names_out())
    mean_scores   = np.asarray(tfidf_matrix.mean(axis=0)).flatten()

    print(f"✅ TF-IDF ready — {len(df_tfidf):,} books, {len(feature_names):,} terms")
    return df_tfidf, tfidf_matrix, feature_names, mean_scores


# ── Charts 9–13: TF-IDF analysis ─────────────────────────────────────────────
def chart_09_top_words(feature_names, mean_scores):
    top_idx    = mean_scores.argsort()[-30:][::-1]
    top_words  = feature_names[top_idx]
    top_scores = mean_scores[top_idx]
    fig, ax    = plt.subplots(figsize=(10, 8))
    bars = ax.barh(top_words[::-1], top_scores[::-1],
                   color=sns.color_palette("muted")[0], edgecolor="white")
    ax.set_xlabel("Mean TF-IDF Score")
    ax.set_title("Top 30 Most Important Words Across All Books", fontsize=14, fontweight="bold")
    ax.bar_label(bars, labels=[f"{v:.4f}" for v in top_scores[::-1]], padding=4, fontsize=8)
    ax.set_xlim(0, top_scores.max() * 1.18)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "09_top_tfidf_words.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Chart 9 saved")


def chart_10_words_per_region(df_tfidf, tfidf_matrix, feature_names):
    regions = [r for r in df_tfidf["region"].value_counts().index if r != "Other"]
    n_cols  = 3
    n_rows  = -(-len(regions) // n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, n_rows * 4))
    axes = axes.flatten()
    for i, region in enumerate(regions):
        mask          = df_tfidf["region"] == region
        indices       = np.where(mask)[0]
        region_matrix = tfidf_matrix[indices]
        region_scores = np.asarray(region_matrix.mean(axis=0)).flatten()
        top10_idx     = region_scores.argsort()[-10:][::-1]
        axes[i].barh(feature_names[top10_idx][::-1], region_scores[top10_idx][::-1],
                     color=sns.color_palette("muted")[i % 8], edgecolor="white")
        axes[i].set_title(region, fontsize=11, fontweight="bold")
        axes[i].set_xlabel("Mean TF-IDF Score")
    for j in range(len(regions), len(axes)):
        axes[j].set_visible(False)
    plt.suptitle("Top 10 Most Distinctive Words per Region", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "10_tfidf_words_per_region.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Chart 10 saved")


def chart_11_wordcloud(feature_names, mean_scores):
    word_scores = dict(zip(feature_names, mean_scores))
    wc = WordCloud(width=1400, height=700, background_color="white",
                   colormap="viridis", max_words=150, prefer_horizontal=0.85)
    wc.generate_from_frequencies(word_scores)
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Word Cloud — Non-Western Fantasy Themes", fontsize=16, fontweight="bold", pad=15)
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "11_wordcloud.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Chart 11 saved")


def chart_12_scatter(df_tfidf, tfidf_matrix):
    print("Running UMAP...")
    reducer   = umap.UMAP(n_components=2, n_neighbors=20, min_dist=0.02,
                          metric="cosine", random_state=42)
    embedding = reducer.fit_transform(tfidf_matrix)

    print("Running HDBSCAN...")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=25, min_samples=5, metric="euclidean")
    labels    = clusterer.fit_predict(embedding)
    df_tfidf["cluster"] = labels

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise    = (labels == -1).sum()
    print(f"Found {n_clusters} clusters, {n_noise} noise points")

    # Print cluster summary
    for cid in sorted(set(labels)):
        if cid == -1: continue
        mask = df_tfidf["cluster"] == cid
        print(f"  Cluster {cid} ({mask.sum()} books): "
              f"{df_tfidf[mask]['region'].value_counts().head(2).to_dict()}")

    cluster_labels = {
        0: "Black Panther comics",
        1: "Short fiction & novellas",
        2: "Chinese web novels",
        3: "General non-western fantasy",
    }
    label_offsets = {0: (0, -1.5), 1: (0, 1.5), 2: (0, 1.5), 3: (0, 2.5)}

    # Chart 12a — HDBSCAN clusters
    palette = sns.color_palette("tab10", max(n_clusters, 1))
    colors  = [palette[l % 10] if l >= 0 else (0.7, 0.7, 0.7) for l in labels]
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.scatter(embedding[:, 0], embedding[:, 1], c=colors, s=15, alpha=0.7, linewidths=0)
    for cid in range(n_clusters):
        mask   = labels == cid
        cx, cy = embedding[mask, 0].mean(), embedding[mask, 1].mean()
        ox, oy = label_offsets.get(cid, (0, 1.5))
        ax.text(cx + ox, cy + oy,
                f"{cluster_labels.get(cid, f'Cluster {cid}')}\n({mask.sum()} books)",
                fontsize=9, fontweight="bold", ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85, ec="gray"))
    legend_elements = [mpatches.Patch(facecolor=palette[i], label=cluster_labels.get(i, f"Cluster {i}"))
                       for i in range(n_clusters)] + \
                      [mpatches.Patch(facecolor=(0.7, 0.7, 0.7), label="Noise")]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9, framealpha=0.8)
    ax.set_title("HDBSCAN Clusters — Thematic Map of Non-Western Fantasy", fontsize=14, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "12a_hdbscan_clusters.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Chart 12a saved")

    # Chart 12b — Heritage regions
    unique_regions = sorted(set(df_tfidf["region"].tolist()))
    region_palette = dict(zip(unique_regions, sns.color_palette("tab10", len(unique_regions))))
    region_colors  = [region_palette[r] for r in df_tfidf["region"].tolist()]
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.scatter(embedding[:, 0], embedding[:, 1], c=region_colors, s=15, alpha=0.7, linewidths=0)
    legend_elements = [mpatches.Patch(facecolor=region_palette[r], label=r) for r in unique_regions]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=9, framealpha=0.8)
    ax.set_title("Heritage Regions — Thematic Map of Non-Western Fantasy", fontsize=14, fontweight="bold")
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "12b_heritage_regions.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Chart 12b saved")

    return embedding, labels


def chart_13_synonyms(feature_names, mean_scores):
    vocab_set       = set(feature_names)
    word_score_dict = dict(zip(feature_names, mean_scores))
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()
    for i, (group_name, synonyms) in enumerate(SYNONYM_GROUPS.items()):
        present = [w for w in synonyms if w in vocab_set]
        absent  = [w for w in synonyms if w not in vocab_set]
        scores  = [word_score_dict[w] for w in present]
        bars    = axes[i].bar(present, scores,
                              color=[sns.color_palette("muted")[i % 8]] * len(present),
                              edgecolor="white")
        axes[i].bar_label(bars, labels=[f"{v:.4f}" for v in scores], padding=3, fontsize=8)
        axes[i].set_title(f'"{group_name}" synonyms', fontsize=11, fontweight="bold")
        axes[i].set_ylabel("Mean TF-IDF Score")
        axes[i].tick_params(axis="x", rotation=30)
        if scores:
            axes[i].set_ylim(0, max(scores) * 1.2)
        if absent:
            axes[i].set_xlabel(f"Not in vocabulary: {', '.join(absent)}", fontsize=8, color="gray")
    plt.suptitle("Synonym Groups — Are Related Words Treated Separately by TF-IDF?",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "13_synonym_analysis.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Chart 13 saved")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    df = load_data()

    # Dataset overview charts
    chart_01_books_by_region(df)
    chart_02_publication_years(df)
    chart_03_ratings(df)
    chart_04_top_authors(df)
    chart_05_most_rated(df)
    chart_06_coverage(df)
    chart_07_rating_by_region(df)
    chart_08_top_tags(df)

    # TF-IDF charts
    df_tfidf, tfidf_matrix, feature_names, mean_scores = build_tfidf(df)
    chart_09_top_words(feature_names, mean_scores)
    chart_10_words_per_region(df_tfidf, tfidf_matrix, feature_names)
    chart_11_wordcloud(feature_names, mean_scores)
    chart_12_scatter(df_tfidf, tfidf_matrix)
    chart_13_synonyms(feature_names, mean_scores)

    print(f"\n🎉 All 13 charts saved to {REPORTS_DIR}")


if __name__ == "__main__":
    main()
