# 🌍 The Other Shelf — Non-Western Fantasy Book Recommender

> *Everyone reads the same 10 books. This recommender helps you find something amazing from a different heritage.*

A content-based book recommender that surfaces lesser-known non-western fantasy and science fiction — from African mythology and Japanese folklore to Andean gods, Indigenous dreamtime, Arabian djinn and much more.

---

## 📖 Project Overview

This project was built as part of the Ironhack Data Analytics bootcamp. The goal was to collect, clean, and model a dataset of non-western fantasy books, then build a Streamlit recommender app that helps readers discover books beyond the western canon.

**3,229 books** across 7 heritage regions:
🌍 Africa & Diaspora · ⛩️ Asia · 🕌 Middle East · 🌿 Indigenous · 🌊 Oceania · 🌺 South Asia · 🌎 Latin America

---

## 🗂️ Project Structure

```
Book-recommendations/
├── Data/
│   ├── Raw/
│   │   └── non_western_fantasy/
│   │       ├── ol_genre_first.json          # Open Library raw data
│   │       └── goodreads_with_descriptions.csv  # Goodreads scraped data
│   └── Clean/
│       ├── merged_non_western_fantasy.json  # Final cleaned dataset
│       └── merged_non_western_fantasy.csv
├── Models/
│   ├── books_index.json                     # Books metadata for Streamlit
│   ├── tfidf_matrix.npz                     # Serialized TF-IDF matrix
│   └── vectorizer.pkl                       # Serialized TF-IDF vectorizer
├── Notebooks/
│   └── Exploratory/
│       ├── 01_api_collector_fantasy.ipynb   # Open Library API collection
│       ├── 02_goodreads_scraper_fantasy.ipynb # Goodreads Selenium scraper
│       ├── 03_merge_and_clean_fantasy.ipynb # Cleaning & merging pipeline
│       ├── 04_eda_fantasy.ipynb             # Exploratory Data Analysis
│       └── 05_recommender_fantasy.ipynb     # TF-IDF recommender model
├── Reports/
│   └── EDA-Fantasy/                         # Saved EDA charts
├── Streamlit/
│   └── Pages/
│       └── World_Fantasy.py                 # Streamlit app page
└── README.md
```

---

## 🔧 Pipeline

### Notebook 01 — Open Library API Collector
Collects books from the [Open Library API](https://openlibrary.org/developers/api) using 52 genre-subject queries targeting non-western fantasy themes (e.g. `fantasy yoruba`, `fantasy djinn`, `wuxia`, `afrofuturism`). Books are tagged with a `source_tag` indicating their heritage region. Includes checkpoint/resume functionality to handle rate limits.

**Output:** `ol_genre_first.json` (~1,500+ books after cleaning)

### Notebook 02 — Goodreads Scraper
Scrapes 10 Goodreads community shelves (e.g. `african-fantasy`, `asian-fantasy`, `afrofuturism`) using Selenium for pagination and description fetching. Requires manual Goodreads login in the browser window before scraping.

**Output:** `goodreads_with_descriptions.csv` (~2,100 books)

### Notebook 03 — Merge, Filter & Clean
The core cleaning pipeline:
- Applies the same nonfiction/noise filter to both data sources (removes western authors, coloring books, biographies, comics)
- Merges Goodreads and Open Library data (Goodreads wins on overlaps)
- Enriches missing descriptions via Google Books API and OpenLibrary API
- Applies English-language filter using `langdetect`
- Deduplicates and cleans titles/datatypes
- Final save to `merged_non_western_fantasy.json`

**Output:** `merged_non_western_fantasy.json` (3,229 books)

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
- Constructs a `text` field combining description + subjects + title + author (title/author weighted x2)
- Applies synonym normalization (e.g. `witch/mage/wizard → magic_user`, `king/queen/emperor → royalty`)
- Fits a TF-IDF vectorizer (5,000 features, custom stopwords, bigrams)
- Implements a three-lane recommender: *More by this author* / *Similar books* / *Hidden gems from underrepresented regions*
- Serializes model to `Models/` for the Streamlit app

**Output:** `tfidf_matrix.npz`, `vectorizer.pkl`, `books_index.json`

---

## 🤖 Model

**TF-IDF (Term Frequency — Inverse Document Frequency)** with cosine similarity.

Each book description is vectorized into a 5,000-dimension space. Books with similar descriptions produce vectors with a small angle between them (high cosine similarity).

**Key design choices:**
- Custom stopwords remove noise words (`book`, `novel`, `author`, `world`, `life` etc.)
- Synonym normalization groups related concepts so `witch`, `mage` and `sorcerer` are treated as the same signal
- Bigrams (`(1,2)` n-gram range) capture two-word phrases like `arabian nights` and `magic user`
- `min_df=3` removes words appearing in fewer than 3 books

**Known limitations:**
- Purely keyword-based — does not understand semantic meaning beyond synonyms
- Clusters by vocabulary, so foreign-language books may group by language rather than theme
- Large diverse collections are hard to separate into thematic clusters

---

## 🚀 Running the App

```bash
# Install dependencies
uv pip install -r requirements.txt

# Run the Streamlit app
streamlit run Streamlit/Home.py
```

**Requirements:** Python 3.10+, Chrome (for Goodreads scraping)

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
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```
GOOGLE_BOOKS_API_KEY=your_key_here
GOODREADS_EMAIL=your_email
GOODREADS_PASSWORD=your_password
```

The Google Books API key is used for description enrichment in Notebook 03. The Goodreads credentials are used for the Selenium scraper in Notebook 02.

---

## 📊 Dataset Statistics

| Metric | Value |
|--------|-------|
| Total books | 3,229 |
| Books with real descriptions | ~2,900 |
| Unique authors | 1,800+ |
| Heritage regions | 7 |
| Sources | Open Library + Goodreads |
| Year range | 1900 – 2025 |

**Top regions by book count:** Asia · Africa & Diaspora · South Asia · Middle East · Latin America · Indigenous · Oceania

---

## 👩‍💻 Author

Built as part of the Ironhack Data Analytics bootcamp, cohort 2025.
