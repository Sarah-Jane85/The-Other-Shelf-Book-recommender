# 📚 The Other Shelf — Multi-Genre Book Recommender

> *Step off the beaten path. Discover books from traditions the algorithm forgot.*

A suite of three content-based book recommenders built as part of the Ironhack Data Analytics Bootcamp (2026). Each recommender targets a different genre, all connected through a shared Streamlit interface.

---

## 🗂️ Three Recommenders, One App

| Recommender | Focus | Author |
|---|---|---|
| 🌍 **World Fantasy** | Non-western fantasy & sci-fi from 7 heritage regions | Sarah Jane Nede |
| 📖 **Non-Fiction** | *[description coming soon]* | Gonçalo Trindade |
| 🎨 **Graphic Novels** | *[description coming soon]* | Rachel Vianna |

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

## 🗂️ Project Structure

```
Book-recommendations/
├── Data/
│   ├── Clean/
│   │   └── non_fiction
│   ├── Keywords/
│   └── Raw/
├── Models/
│   ├── books_index.json                         # Books metadata for Streamlit
│   ├── tfidf_matrix.npz                         # Serialized TF-IDF matrix
│   └── vectorizer.pkl                           # Serialized TF-IDF vectorizer
├── Notebooks/
│   └── 
├── Reports/
│   ├── EDA-Fantasy/
│   ├── EDA-Graphic-Novels/
│   └── EDA-Non-Fiction/
├── Src/
│   ├── 01_api_collector_fantasy.py
│   ├── 02_goodreads_scraper_fantasy.py
│   ├── 03_merge_and_clean_fantasy.py
│   ├── 04_eda_fantasy.py
│   └── 05_recommender_fantasy.py
├── Streamlit/
│   ├── Assets/
│   │   ├── book_fantasy.png
│   │   ├── book_graphic.png
│   │   └── book_nonfiction.png
│   ├── Components/
│   │   └── shared.py
│   ├── Pages/
│   │   └── World_Fantasy.py
│   ├── Home.py
│   └── config.yaml
├── .env
├── pyproject.toml
└── README.md
```

---

## 🤖 Shared Model Architecture

All three recommenders use the same core approach:

**TF-IDF (Term Frequency — Inverse Document Frequency)** with cosine similarity.

Each book's description, subjects, title and author are vectorized into a high-dimensional space. Books with similar content produce vectors with a small angle between them (high cosine similarity), which is used to surface recommendations.

**Common design choices:**
- Custom stopwords remove noise words (`book`, `novel`, `author`, `world`, `life`, etc.)
- Bigrams (`(1,2)` n-gram range) capture meaningful two-word phrases
- `min_df=3` removes words appearing in fewer than 3 books
- Model artifacts serialized to `Models/` for use in the Streamlit app

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

> *[Tagline / short description — to be filled in]*

*[Short project description — to be filled in]*

## 🔧 Pipeline

### Notebook 01 — Data Collection
*[Description — to be filled in]*

### Notebook 02 — Data Cleaning
*[Description — to be filled in]*

### Notebook 03 — Exploratory Data Analysis
*[Description — to be filled in]*

### Notebook 04 — TF-IDF Recommender
*[Description — to be filled in]*

## 📊 Dataset Statistics

| Metric | Value |
|--------|-------|
| Total books | *[to be filled in]* |
| Unique authors | *[to be filled in]* |
| Sources | *[to be filled in]* |

---

---

# 🎨 Graphic Novels Recommender

*By Rachel Vianna*

> *[Tagline / short description — to be filled in]*

*[Short project description — to be filled in]*

## 🔧 Pipeline

### Notebook 01 — Data Collection
*[Description — to be filled in]*

### Notebook 02 — Data Cleaning
*[Description — to be filled in]*

### Notebook 03 — Exploratory Data Analysis
*[Description — to be filled in]*

### Notebook 04 — TF-IDF Recommender
*[Description — to be filled in]*

## 📊 Dataset Statistics

| Metric | Value |
|--------|-------|
| Total books | *[to be filled in]* |
| Unique authors | *[to be filled in]* |
| Sources | *[to be filled in]* |

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
