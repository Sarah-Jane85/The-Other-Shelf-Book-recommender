# 📚 The Other Shelf — Multi-Genre Book Recommender

> *Step off the beaten path. Discover books from traditions the algorithm forgot.*

A suite of three content-based book recommenders built as part of the Ironhack Data Analytics Bootcamp (2026). Each recommender targets a different genre, all connected through a shared Streamlit interface.

---

## 🗂️ Three Recommenders, One App

| Recommender | Focus | Author |
|---|---|---|
| 🌍 **World Fantasy** | Non-western fantasy & sci-fi from 7 heritage regions | Sarah Jane Nede |
| 📖 **Non-Fiction** | Left-wing critical theory & postcolonial studies — 39 curated authors | Gonçalo Trindade |
| 🎨 **Graphic Novels** | Narrative graphic novels & literary comics beyond the superhero shelf | Rachel Vianna |

The three recommenders share a Streamlit home page and visual style. From the home page, users select their genre and are taken to the corresponding recommender. Each recommender is built independently using the same TF-IDF + cosine similarity pipeline.

---

## 🚀 Running the App

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run the Streamlit app
streamlit run Streamlit/Home.py
```

**Requirements:** Python 3.13+, Chrome (for Goodreads scraping)

---

## 🔗 Links

| | |
|---|---|
| 🎞️ **Presentation** | [View on Prezi](https://prezi.com/view/zQ1t442K5eAsngtLwpVA/?referral_token=VzXuWplnB3FN) |
| 🚀 **Live App** | [View on Streamlit](https://the-other-shelf-book-recommender.streamlit.app/) |

---

## 🗂️ Project Structure

```
Book-recommendations/
├── Data/
│   ├── Clean/
│   │   ├── graphic_novels/
│   │   ├── non_fiction/
│   │   └── non_western_fantasy/
│   ├── Keywords/
│   │   └── non_western_fantasy_keywords.json
│   └── Raw/
│       ├── graphic_novels/
│       │   └── openlibrary_graphic_novels_raw.csv
│       ├── non_fiction/
│       │   ├── leftpolitics_raw(API).csv
│       │   └── leftpolitics_raw(scraping).csv
│       └── non_western_fantasy/
│           ├── goodreads_raw.csv
│           ├── goodreads_with_descriptions.csv
│           ├── ol_genre_first.json
│           └── ol_genre_first_checkpoint.json
├── Models/
│   ├── fantasy_books_index.json
│   ├── fantasy_tfidf_matrix.npz
│   ├── fantasy_vectorizer.pkl
│   ├── graphic_books_index.json
│   ├── graphic_tfidf_matrix.npz
│   └── graphic_vectorizer.pkl
├── Notebooks/
│   ├── exploratory/
│   ├── graphic_novels/
│   │   ├── 01_api_collector_graphic_novels.ipynb
│   │   ├── 02_google_books_enrichment_graphic_novels.ipynb
│   │   ├── 03_merge_and_clean_graphic_novels.ipynb
│   │   ├── 04_eda_graphic_novels.ipynb
│   │   └── 05_recommender_graphic_novels.ipynb
│   ├── non_fiction/
│   │   ├── actual-scraping.ipynb
│   │   ├── data-cleaning-non-fiction.ipynb
│   │   ├── EDA-non-fiction.ipynb
│   │   ├── final-data-cleaning.ipynb
│   │   ├── non-fiction-API.ipynb
│   │   ├── non-fiction-scraping.ipynb
│   │   └── nonfiction-cleaning-scraping.ipynb
│   └── non_western_fantasy/
│       ├── 01_api_collector_fantasy_clean.ipynb
│       ├── 02_goodreads_scraper_fantasy_clean.ipynb
│       ├── 03_merge_and_clean_fantasy_clean.ipynb
│       ├── 04_eda_fantasy_clean.ipynb
│       └── 05_recommender_fantasy_clean.ipynb
├── Reports/
│   ├── EDA_Graphic_Novels/
│   │   ├── 01_publication_years.png
│   │   ├── 02_top_authors.png
│   │   ├── 03_description_words.png
│   │   └── 04_theme_counts.png
│   ├── EDA-Fantasy/
│   │   ├── 01_books_by_region.png
│   │   ├── 02_publication_years.png
│   │   ├── 03_ratings.png
│   │   ├── 04_top_authors.png
│   │   ├── 05_most_rated.png
│   │   ├── 06_coverage.png
│   │   ├── 07_rating_by_region.png
│   │   ├── 08_top_tags.png
│   │   ├── 09_top_tfidf_words.png
│   │   ├── 10_tfidf_words_per_region.png
│   │   ├── 11_wordcloud.png
│   │   ├── 12_umap_clusters.png
│   │   ├── 12a_hdbscan_clusters.png
│   │   ├── 12b_heritage_regions.png
│   │   └── 13_synonym_analysis.png
│   └── EDA-Non-Fiction/
│       ├── 01_top_authors.png
│       ├── 02_publication_years.png
│       ├── 03_top_unigrams.png
│       ├── 04_top_bigrams.png
│       ├── 05_missing_values.png
│       ├── 06_clustering_metrics.png
│       ├── 07_clusters_pca.png
│       └── 08_cluster_sizes.png
├── Src/
│   ├── 01_api_collector_fantasy.py
│   ├── 02_goodreads_scraper_fantasy.py
│   ├── 03_merge_and_clean_fantasy.py
│   ├── 04_eda_fantasy.py
│   ├── 05_recommender_fantasy.py
│   └── recommender_non_fiction.py
├── Streamlit/
│   ├── assets/
│   │   ├── book_fantasy.png
│   │   ├── book_graphic.png
│   │   └── book_nonfiction.png
│   ├── components/
│   │   ├── nonfiction_utils.py
│   │   └── shared.py
│   ├── pages/
│   │   ├── Graphic_Novels.py
│   │   ├── Non-Fiction.py
│   │   └── World_Fantasy.py
│   └── Home.py
├── .gitignore
├── .python-version
├── config.yaml
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

---

## 🤖 Shared Model Architecture

All three recommenders use the same core approach:

**TF-IDF (Term Frequency — Inverse Document Frequency)** with cosine similarity.

Each book's description, subjects, title and author are vectorized into a high-dimensional space. Books with similar content produce vectors with a small angle between them (high cosine similarity), which is used to surface recommendations.

**Common design choices:**
- Bigrams (`(1,2)` n-gram range) capture meaningful two-word phrases
- Model artifacts serialized to `Models/` for use in the Streamlit app

Note: stopword lists, `min_df`, and feature counts differ per recommender depending on genre needs.

---

---

# 🌍 World Fantasy Recommender

*By Sarah Jane Nede*

> *Everyone reads the same 10 books. This recommender helps you find something amazing from a different heritage.*

A content-based book recommender that surfaces lesser-known non-western fantasy and science fiction — from African mythology and Japanese folklore to Andean gods, Indigenous dreamtime, Arabian djinn and much more.

**3.396 books** across 7 heritage regions:
🌍 Africa & Diaspora · ⛩️ Asia · 🕌 Middle East · 🌿 Indigenous · 🌊 Oceania · 🌺 South Asia · 🌎 Latin America

## 🔧 Pipeline

### Notebook 01 — Open Library API Collector
Collects books from the [Open Library API](https://openlibrary.org/developers/api) using 52 genre-subject queries targeting non-western fantasy themes (e.g. `fantasy yoruba`, `fantasy djinn`, `wuxia`, `afrofuturism`). Books are tagged with a `source_tag` indicating their heritage region. Includes checkpoint/resume functionality to handle rate limits.

**Output:** `ol_genre_first.json` (~1,500+ books after cleaning)

### Notebook 02 — Goodreads Scraper
Scrapes 10 Goodreads community shelves (e.g. `african-fantasy`, `asian-fantasy`, `afrofuturism`) using Selenium for pagination and description fetching. Requires manual Goodreads login in the browser window before scraping.

**Output:** `goodreads_with_descriptions.csv` (~2.100 books)

### Notebook 03 — Merge, Filter & Clean
The core cleaning pipeline:
- Applies the same nonfiction/noise filter to both data sources (removes western authors, coloring books, biographies, comics)
- Merges Goodreads and Open Library data (Goodreads wins on overlaps)
- Enriches missing descriptions via Google Books API and OpenLibrary API
- Applies English-language filter using `langdetect`
- Deduplicates and cleans titles/datatypes

**Output:** `merged_non_western_fantasy.json` (3.396 books)

### Notebook 04 — Exploratory Data Analysis
13 charts exploring the dataset:

| Chart | Description |
|-------|-------------|
| 01 | Books by region |
| 02 | Publication year distribution |
| 03 | Rating distribution & popularity tiers |
| 04 | Top 20 most represented authors |
| 05 | Top 15 most rated books |
| 06 | Dataset coverage (source, descriptions, ratings) |
| 07 | Average rating by region |
| 08 | Top 25 source tags |
| 09 | Top 30 TF-IDF words across all books |
| 10 | Top 10 distinctive words per heritage region |
| 11 | Word cloud of dominant themes |
| 12a | HDBSCAN clustering scatter plot |
| 12b | Heritage regions scatter plot (UMAP) |
| 13 | Synonym group analysis |

### Notebook 05 — TF-IDF Recommender
Builds the content-based recommender:
- Constructs a `text` field combining description + subjects + title + author (title/author weighted ×2)
- Applies synonym normalization (e.g. `witch/mage/wizard → magic_user`, `king/queen/emperor → royalty`)
- Fits a TF-IDF vectorizer (5,000 features, custom stopwords, bigrams)
- Implements a three-lane recommender: *More by this author* / *Similar books* / *Hidden gems from underrepresented regions*
- Serializes model to `Models/` for the Streamlit app

**Output:** `tfidf_matrix.npz`, `vectorizer.pkl`, `books_index.json`

## 📊 Dataset Statistics

| Metric | Value |
|--------|-------|
| Total books | 3.396 |
| Books with real descriptions | ~2.900 |
| Unique authors | 1.800+ |
| Heritage regions | 7 |
| Sources | Open Library + Goodreads |
| Year range | 1900 – 2025 |

**Top regions by book count:** Asia · Africa & Diaspora · South Asia · Middle East · Latin America · Indigenous · Oceania

---

---

# 📖 Non-Fiction Recommender

*By Gonçalo Trindade*

> *The algorithm won't show you these. We will.*

A content-based recommender for left-wing non-fiction — critical theory, postcolonial studies, feminist thought, Marxist analysis, and radical perspectives that mainstream platforms consistently overlook. Search by keyword, topic, author, or title to find your next read across **2,960 books** from 39 curated thinkers.

## 🔧 Pipeline

### Notebook 01 — Data Collection (Open Library API)
Queries the [Open Library API](https://openlibrary.org/developers/api) (`search.json`) author by author across 39 curated thinkers — from Angela Davis and Frantz Fanon to David Graeber and Mark Fisher. Up to 50 results per author, filtered to only keep works where the queried author is actually listed. Includes a 0.5s polite delay between requests.

**Output:** `leftpolitics_raw(API).csv` (~1,316 records)

### Notebook 02 — Data Collection (Goodreads Scraping) + Description Enrichment
Scrapes Goodreads search results using `curl` + BeautifulSoup for the same 39 authors, paginating up to 10 pages per author. Then visits each book's individual Goodreads page to fetch the full synopsis, saving progress every 50 books for resilience against interruptions.

**Output:** `leftpolitics_raw(scraping).csv` (~5,187 records) + `leftpolitics_with_descriptions.csv` (~5,487 records, after description enrichment)

### Notebook 03 — Data Cleaning
Merges and cleans the two sources:
- Strips whitespace and standardises author name casing
- Drops the `subjects` column (100% null from scraping)
- Drops rows missing title, author, or description (1,314 books had no synopsis)
- Language detection with `langdetect` — keeps English only (1,211 non-English books removed)
- Deduplication on title + author

**Output:** `leftpolitics_final_clean.csv` (2,960 books)

### Notebook 04 — Exploratory Data Analysis
8 charts exploring the dataset: top authors by book count, publication year distribution, top unigrams and bigrams from descriptions, missing value overview, KMeans clustering metrics (elbow method), PCA cluster scatter plot, and cluster size distribution.

### Notebook 05 — TF-IDF Recommender
Builds the content-based recommender:
- Constructs a `corpus` field combining title + author + description
- Fits a TF-IDF vectorizer (25,000 features, English stopwords, bigrams `(1,2)`)
- Recommends by cosine similarity between the query vector and every book in the index
- Returns top-N results with score > 0, deployed via Streamlit

**Output:** used directly by the Streamlit app via `recommender_non_fiction.py`
> *Critical theory, postcolonial thought, and left-wing non-fiction — the books that challenge how you see the world.*

A content-based recommender focused on left-wing non-fiction, critical theory, and postcolonial studies. Built around a curated list of 39 authors — from Angela Davis and Frantz Fanon to David Graeber and Mark Fisher — spanning Black American thought, African and Caribbean theory, feminist and queer theory, Latin American perspectives, and contemporary left politics.

**3,034 books** across left-wing, critical theory, and postcolonial studies.

## 🔧 Pipeline

### Notebook 01 — Open Library API Collector
Fetches books by 39 curated left-wing and critical theory authors from the [Open Library API](https://openlibrary.org/developers/api). Only books where the queried author is actually listed are kept. Includes authors across traditions: Black American thinkers (Angela Davis, Audre Lorde, W.E.B. Du Bois), African & Caribbean theorists (Frantz Fanon, C.L.R. James, Achille Mbembe), Latin American voices (Paulo Freire, Eduardo Galeano), feminist & queer theory (bell hooks, Silvia Federici, Sara Ahmed), and contemporary left (David Graeber, Mark Fisher, Slavoj Žižek).

**Output:** `leftpolitics_raw.csv`

### Notebook 02 — Goodreads Scraper
Scrapes Goodreads search results for the same 39 authors using `curl` + BeautifulSoup. Paginates through each author's book list and enriches with full descriptions from individual book pages. Includes checkpoint/resume functionality.

**Output:** `leftpolitics_with_descriptions.csv`

### Notebook 03 — Data Cleaning
Two-stage cleaning pipeline:
- Basic cleaning: strips whitespace, standardizes author names, fills missing authors from `queried_author`, drops rows missing title/author, deduplicates
- Final cleaning: drops rows missing descriptions, applies English-language filter using `langdetect`, drops `subjects` column (100% null), resets index

**Output:** `leftpolitics_final_clean.csv`

### Notebook 04 — Exploratory Data Analysis
5 analyses exploring the dataset:

| Chart | Description |
|-------|-------------|
| 01 | Top 15 authors by book count |
| 02 | Publication year distribution |
| 03 | Top 20 single-word topics (CountVectorizer) |
| 04 | Top 20 two-word topic phrases |
| 05 | Word cloud of titles + descriptions |
| 06 | K-Means clustering (elbow + silhouette, k=5) |
| 07 | PCA cluster visualization |

### Notebook 05 — TF-IDF Recommender
Builds the content-based recommender using the same shared pipeline as the other recommenders — TF-IDF vectorizer on combined title + description text, cosine similarity for recommendations.

**Output:** `nonfiction_vectorizer.pkl`, `nonfiction_tfidf_matrix.npz`, `nonfiction_books_index.json`


## 📊 Dataset Statistics

| Metric | Value |
|--------|-------|
| Total books | 2,960 |
| Curated thinkers queried | 39 |
| Sources | Open Library API + Goodreads (scraping) |
| Year range | 1798 – 2026 |
| Raw records collected | ~6,800 |
| Non-English books removed | 1,211 |
| Books dropped (no description) | 1,314 |
| Total books | 3,034 |
| Curated authors | 39 |
| Sources | Open Library + Goodreads |
| Top topics | capitalism · colonialism · race · labor · decolonization |
| Traditions covered | Black American · African & Caribbean · Latin American · Feminist · Contemporary Left |

---

---

# 🎨 Graphic Novels Recommender

*By Rachel Vianna*

> *Sequential art beyond the mainstream — because the best stories aren't always told in words.*

A content-based recommender for graphic novels, graphic memoirs and literary comics. Built for readers who want to discover serious, narrative-driven graphic works beyond the superhero shelf — from war memoirs and political histories to coming-of-age stories and visual autobiographies.

**351 books** sourced from Open Library, enriched with descriptions and filtered down to narrative graphic works only.

## 🔧 Pipeline

### Notebook 01 — Open Library API Collector
Collects graphic novel candidates from the [Open Library API](https://openlibrary.org/developers/api) using 10 search terms (`graphic novel`, `sequential art`, `graphic memoir`, `illustrated novel`, `visual storytelling`, etc.). Deduplicates on title + author.

**Output:** `openlibrary_graphic_novels_raw.csv` (~5,609 books raw)

### Notebook 02 — Description Enrichment
Fetches descriptions for all books from the Open Library works API using each book's `ol_key`. Saves enriched dataset for cleaning.

**Output:** `graphic_novels_with_descriptions.csv` (5,609 books, ~3,409 missing descriptions filled where available)

### Notebook 03 — Merge, Filter & Clean
Core cleaning pipeline:
- Drops rows missing title, author, or description
- Deduplicates on title + author
- Filters to include only genuine graphic works (must contain terms like `graphic novel`, `sequential art`, `graphic memoir`, `illustrated`, `cartoon`)
- Excludes noise: how-to guides, drawing tutorials, theory/criticism, coloring books, children's content, animation books
- Filters further to narrative works using story keywords (`story`, `memoir`, `war`, `family`, `coming of age`, etc.)
- Cleans and normalizes text for the model

**Output:** `merged_graphic_novels.csv` (351 books)

### Notebook 04 — Exploratory Data Analysis
4 charts exploring the dataset:

| Chart | Description |
|-------|-------------|
| 01 | Publication year distribution |
| 02 | Top authors by book count |
| 03 | Most common words in descriptions |
| 04 | Recurring themes (memoir, war, family, identity, politics…) |

### Notebook 05 — TF-IDF Recommender
Builds the content-based recommender:
- Constructs `combined_text` from description (weighted ×2) + title + author
- Fits a TF-IDF vectorizer (8,000 features, English stopwords)
- Cosine similarity used to rank and return top-N recommendations
- Serializes model to `Models/` for the Streamlit app

**Output:** `graphic_vectorizer.pkl`, `graphic_tfidf_matrix.npz`, `graphic_books_index.json`

## 📊 Dataset Statistics

| Metric | Value |
|--------|-------|
| Total books | 351 |
| Raw books collected | 5,609 |
| Sources | Open Library |
| Year range | varies |
| Top themes | memoir · war · family · identity · politics |

---

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```
GOOGLE_BOOKS_API_KEY=your_key_here
GOODREADS_EMAIL=your_email
GOODREADS_PASSWORD=your_password
```

The Google Books API key is used for description enrichment. The Goodreads credentials are used for the Selenium scraper.

---

## 📦 Dependencies

```
pandas
numpy
scikit-learn
scipy
streamlit
selenium
beautifulsoup4
requests
langdetect
python-dotenv
wordcloud
umap-learn
hdbscan
tqdm
plotly
seaborn
matplotlib
```

---

## 👩‍💻 Authors

Built as part of the Ironhack Data Analytics Bootcamp, cohort 2026.

- **Sarah Jane Nede** — World Fantasy Recommender
- **Gonçalo Trindade** — Non-Fiction Recommender
- **Rachel Vianna** — Graphic Novels Recommender
