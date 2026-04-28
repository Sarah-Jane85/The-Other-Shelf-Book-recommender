"""
save_plots.py
─────────────
Generates and saves all EDA plots for the Non-Fiction dataset.
Run from anywhere — paths are resolved relative to this file.

Output: numbered PNGs in the same folder as this script.
"""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE      = Path(__file__).resolve().parent
ROOT      = HERE.parents[1]          # Book-recommendations/
DATA_PATH = ROOT / "Data" / "non fiction" / "leftpolitics_final_clean.csv"

def save(fig, name):
    path = HERE / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {name}")

# ── Load ──────────────────────────────────────────────────────────────────────
print(f"Loading data from {DATA_PATH} ...")
df = pd.read_csv(DATA_PATH)
print(f"  {len(df):,} books loaded.\n")

# ── Plot 1 — Top 15 authors ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))
top_authors = df["author"].value_counts().head(15)
sns.barplot(x=top_authors.values, y=top_authors.index, palette="mako", ax=ax)
ax.set_title("Top 15 Authors by Number of Books")
ax.set_xlabel("Book count")
ax.set_ylabel("Author")
fig.tight_layout()
save(fig, "01_top_authors.png")

# ── Plot 2 — Publication year distribution ────────────────────────────────────
year = pd.to_numeric(df["year_published"], errors="coerce")
fig, ax = plt.subplots(figsize=(10, 5))
sns.histplot(year.dropna(), bins=25, kde=False, color="#F5D78E", ax=ax)
ax.set_title("Publication Year Distribution")
ax.set_xlabel("Year published")
ax.set_ylabel("Number of titles")
fig.tight_layout()
save(fig, "02_publication_years.png")

# ── Build term matrix (shared by plots 3, 4, 6, 7, 8) ────────────────────────
print("Building term matrix (used for topic and clustering plots)...")
text_data = (df["title"].fillna("") + " " + df["description"].fillna("")).astype(str)
vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2), max_features=2500)
X = vectorizer.fit_transform(text_data)
terms      = vectorizer.get_feature_names_out()
sums       = np.asarray(X.sum(axis=0)).flatten()
term_freq  = (
    pd.DataFrame({"term": terms, "count": sums})
    .sort_values("count", ascending=False)
)

# ── Plot 3 — Top 20 single-word topics ────────────────────────────────────────
unigrams = term_freq[term_freq["term"].str.count(" ") == 0].head(20)
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(x="count", y="term", data=unigrams, palette="rocket", ax=ax)
ax.set_title("Top 20 Single-Word Topics")
ax.set_xlabel("Frequency")
ax.set_ylabel("Term")
fig.tight_layout()
save(fig, "03_top_unigrams.png")

# ── Plot 4 — Top 20 two-word topics ──────────────────────────────────────────
bigrams = term_freq[term_freq["term"].str.count(" ") == 1].head(20)
fig, ax = plt.subplots(figsize=(10, 7))
sns.barplot(x="count", y="term", data=bigrams, palette="crest", ax=ax)
ax.set_title("Top 20 Two-Word Topics")
ax.set_xlabel("Frequency")
ax.set_ylabel("Phrase")
fig.tight_layout()
save(fig, "04_top_bigrams.png")

# ── Plot 5 — Missing value coverage ──────────────────────────────────────────
missing_pct = df.isna().mean().sort_values(ascending=False) * 100
missing_pct = missing_pct[missing_pct > 0]
fig, ax = plt.subplots(figsize=(8, max(4, len(missing_pct) * 0.5)))
sns.barplot(x=missing_pct.values, y=missing_pct.index, palette="flare", ax=ax)
ax.set_title("Missing Values by Column (%)")
ax.set_xlabel("% missing")
ax.axvline(x=50, color="red", linestyle="--", alpha=0.5, label="50 % threshold")
ax.legend()
fig.tight_layout()
save(fig, "05_missing_values.png")

# ── Plot 6 — Elbow + silhouette for KMeans ───────────────────────────────────
print("Computing clustering metrics (this may take a moment)...")
inertias, silhouettes, K_range = [], [], range(3, 11)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X, km.labels_))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
ax1.plot(list(K_range), inertias, "bo-", linewidth=2, markersize=8)
ax1.set_xlabel("Number of clusters (k)")
ax1.set_ylabel("Inertia")
ax1.set_title("Elbow Method")
ax1.grid(True, alpha=0.3)

ax2.plot(list(K_range), silhouettes, "go-", linewidth=2, markersize=8)
ax2.set_xlabel("Number of clusters (k)")
ax2.set_ylabel("Silhouette score")
ax2.set_title("Silhouette Score by k")
ax2.grid(True, alpha=0.3)

fig.tight_layout()
save(fig, "06_clustering_metrics.png")

# ── Plot 7 — PCA cluster visualisation ───────────────────────────────────────
optimal_k = 5
km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df["cluster"] = km.fit_predict(X)

pca     = PCA(n_components=2, random_state=42)
X_pca   = pca.fit_transform(X.toarray())

fig, ax = plt.subplots(figsize=(12, 7))
sc = ax.scatter(
    X_pca[:, 0], X_pca[:, 1],
    c=df["cluster"], cmap="viridis",
    s=40, alpha=0.6, edgecolors="black", linewidth=0.3,
)
fig.colorbar(sc, ax=ax, label="Cluster")
ax.set_title("Book Clusters — PCA Visualisation", fontsize=14, fontweight="bold")
ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)")
ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)")
fig.tight_layout()
save(fig, "07_clusters_pca.png")

# ── Plot 8 — Cluster size distribution ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 4))
cluster_counts = df["cluster"].value_counts().sort_index()
sns.barplot(x=cluster_counts.index, y=cluster_counts.values, palette="viridis", ax=ax)
ax.set_title(f"Books per Cluster (k={optimal_k})")
ax.set_xlabel("Cluster")
ax.set_ylabel("Number of books")
for bar, count in zip(ax.patches, cluster_counts.values):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 10,
        str(count), ha="center", va="bottom", fontsize=10,
    )
fig.tight_layout()
save(fig, "08_cluster_sizes.png")

print(f"\nAll plots saved to {HERE}")
