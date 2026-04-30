# ── Pages/Graphic_Novels.py ────────────────────────────────────────────────
import json
import pickle
import sys
from pathlib import Path

import pandas as pd
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

# ── Paths ───────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "Models"

sys.path.append(str(Path(__file__).resolve().parents[1]))

from Components.shared import set_page_style, back_button, show_author_bio, get_author_bio

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Graphic Novels — The Other Shelf",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

set_page_style()
back_button()

# ── Load model ──────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    df = pd.DataFrame(
        json.load(open(MODEL_DIR / "graphic_books_index.json", encoding="utf-8"))
    )

    tfidf_matrix = sparse.load_npz(MODEL_DIR / "graphic_tfidf_matrix.npz")

    with open(MODEL_DIR / "graphic_vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)

    return df, tfidf_matrix, vectorizer


df, tfidf_matrix, vectorizer = load_model()

# ── Safety columns ──────────────────────────────────────────────────────────
for col in ["title", "author", "description", "cover_url", "combined_text"]:
    if col not in df.columns:
        df[col] = ""

if "first_publish_year" not in df.columns:
    df["first_publish_year"] = None

if "avg_rating" not in df.columns:
    df["avg_rating"] = None

if "num_ratings" not in df.columns:
    df["num_ratings"] = None

if "source_url" not in df.columns:
    df["source_url"] = ""

if "source" not in df.columns:
    df["source"] = "Open Library"

df["title"] = df["title"].fillna("")
df["author"] = df["author"].fillna("Unknown author")
df["description"] = df["description"].fillna("")
df["cover_url"] = df["cover_url"].fillna("")
df["source_url"] = df["source_url"].fillna("")

# ── Helper functions ────────────────────────────────────────────────────────
def safe(text):
    if pd.isna(text):
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def similarity_label(score):
    if score >= 0.30:
        return "Almost identical"
    if score >= 0.15:
        return "Very similar"
    if score >= 0.08:
        return "Similar"
    if score >= 0.04:
        return "Loosely related"
    return "Inspired by"


def get_rating_text(book):
    rating = book.get("avg_rating", None)
    num_ratings = book.get("num_ratings", None)

    r = f"⭐ {rating}" if pd.notna(rating) and rating else ""
    n = (
        f"· {int(num_ratings):,} ratings"
        if pd.notna(num_ratings) and num_ratings and num_ratings > 0
        else ""
    )

    return r, n


# ── Book detail dialog ──────────────────────────────────────────────────────
@st.dialog("Book Details", width="large")
def show_book_dialog(book):
    title = safe(book.get("title", ""))
    author = safe(book.get("author", ""))

    st.markdown(
        f"""
        <h2 style="color:#F5D78E; margin:0 0 0.25rem 0;">{title}</h2>
        <p style="color:#D4C5A9; font-size:1rem; margin:0 0 1rem 0;">
            by {author}
        </p>
        """,
        unsafe_allow_html=True,
    )

    rating, num = get_rating_text(book)

    year = book.get("first_publish_year", "")
    year_text = f"· First published {int(year)}" if pd.notna(year) and year else ""

    st.markdown(
        f"""
        <p style="color:#D4C5A9; font-size:0.9rem;">
            {rating} {num} {year_text}
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    tab1, tab2 = st.tabs(["📖 Description", "👤 Author Bio"])

    with tab1:
        desc = book.get("description", "")

        if desc and len(str(desc)) > 20:
            st.markdown(
                f"""
                <p style="color:#F5F0E8; font-size:1rem; line-height:1.8;">
                    {safe(str(desc))}
                </p>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<p style='color:#D4C5A9;'>No description available.</p>",
                unsafe_allow_html=True,
            )

        if book.get("source_url"):
            st.markdown(f"[View on {book.get('source', 'source')} →]({book['source_url']})")

    with tab2:
        bio = get_author_bio(book.get("author", ""))

        if bio and bio.get("extract"):
            col_text, col_img = st.columns([3, 1])

            with col_text:
                st.markdown(
                    f"""
                    <p style="color:#F5F0E8; font-size:0.95rem; line-height:1.8;">
                        {safe(bio['extract'][:600])}...
                    </p>
                    <a href="{bio['url']}" target="_blank"
                       style="color:#A8D5B5; font-size:0.85rem;">
                        Read more on Wikipedia →
                    </a>
                    """,
                    unsafe_allow_html=True,
                )

            with col_img:
                if bio.get("image"):
                    st.image(bio["image"], width=130)
        else:
            st.markdown(
                f"<p style='color:#D4C5A9;'>No Wikipedia page found for {safe(book.get('author', ''))}.</p>",
                unsafe_allow_html=True,
            )


# ── Recommender ─────────────────────────────────────────────────────────────
def recommend_three_lanes(query, df, tfidf_matrix, vectorizer, search_by="title", top_n=5):
    if search_by in ("title", "author"):
        col = "title" if search_by == "title" else "author"
        matches = df[df[col].str.contains(query, case=False, na=False)]

        if len(matches) == 0:
            return None, pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        idx = matches.index[0]
        query_book = df.iloc[idx]
        query_vec = tfidf_matrix[idx]
        query_author = str(query_book["author"]).lower().strip()

    else:
        query_vec = vectorizer.transform([query])
        query_book = None
        query_author = ""
        idx = None

    sim_scores = cosine_similarity(query_vec, tfidf_matrix).flatten()

    results = df.copy()
    results["similarity"] = sim_scores

    if idx is not None:
        results = results.drop(index=idx)

    same_author = (
        results[results["author"].str.lower().str.strip() == query_author]
        .sort_values("similarity", ascending=False)
        .head(top_n)
        if query_author
        else pd.DataFrame()
    )

    similar = (
        results[results["author"].str.lower().str.strip() != query_author]
        .sort_values("similarity", ascending=False)
        .head(top_n)
    )

    literary_terms = [
        "memoir",
        "history",
        "identity",
        "family",
        "war",
        "politics",
        "trauma",
        "memory",
        "autobiography",
        "literary",
        "art",
    ]

    hidden_pool = results[
        results["combined_text"].str.contains("|".join(literary_terms), case=False, na=False)
        & (results["author"].str.lower().str.strip() != query_author)
        & (results["similarity"] >= 0.02)
    ]

    hidden_gems = hidden_pool.sort_values("similarity", ascending=False).head(top_n)

    return query_book, same_author, similar, hidden_gems


# ── Header ─────────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div style="text-align:center; padding:1.5rem 0 1rem 0;">
        <h1 style="font-size:3rem; color:#F5F0E8;
                   text-shadow:2px 2px 8px rgba(0,0,0,0.8);">
            Graphic Novels
        </h1>
        <p style="font-size:1.05rem; color:#D4C5A9; margin-bottom:0.75rem;">
            Long-form visual storytelling for adult readers
        </p>
        <p style="font-size:1rem; color:#F5F0E8; max-width:700px;
                  margin:0 auto; line-height:1.8;
                  background:rgba(0,0,0,0.5); padding:1rem 1.5rem;
                  border-radius:10px;">
            Graphic novels are often dismissed as light reading or children's entertainment.
            This recommender highlights books that use image and text to explore memory,
            politics, family, identity, history, trauma, humor and art.
            <strong style="color:#F5D78E;">{len(df):,} books</strong>
            from the world of sequential storytelling.
        </p>
        <p style="color:#D4C5A9; font-size:0.9rem; margin-top:0.75rem;">
            🎨 Visual storytelling &nbsp;·&nbsp; 📖 Memoir &nbsp;·&nbsp; 🕯️ History
            &nbsp;·&nbsp; 🧠 Identity &nbsp;·&nbsp; 🌍 Politics &nbsp;·&nbsp; 🖋️ Literary comics
        </p>
    </div>
    <hr style="border-color:rgba(255,255,255,0.15); margin-bottom:1.5rem;">
    """,
    unsafe_allow_html=True,
)

# ── Layout ─────────────────────────────────────────────────────────────────
middle, right = st.columns([3, 1])

# ── Session state ───────────────────────────────────────────────────────────
if "query_book" not in st.session_state:
    st.session_state.query_book = None
if "same_author" not in st.session_state:
    st.session_state.same_author = pd.DataFrame()
if "similar" not in st.session_state:
    st.session_state.similar = pd.DataFrame()
if "hidden_gems" not in st.session_state:
    st.session_state.hidden_gems = pd.DataFrame()
if "no_results" not in st.session_state:
    st.session_state.no_results = False
if "selected_book" not in st.session_state:
    st.session_state.selected_book = None

# ══ MIDDLE ═══════════════════════════════════════════════════════════════════
with middle:
    st.markdown(
        """
        <style>
            div[data-testid="stButton"] {
                max-width: 700px;
                margin: 0 auto;
            }
            div[data-testid="stTextInput"] {
                max-width: 700px;
                margin: 0 auto;
            }
            div[data-testid="stRadio"] {
                max-width: 700px;
                margin: 0 auto;
            }
            div[data-testid="stHorizontalBlock"] {
                max-width: 700px;
                margin: 0 auto;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_l, col_radio, col_r = st.columns([1.6, 3.8, 1.6])

    with col_radio:
        search_mode = st.radio(
            "Search by:",
            ["Book title", "Author", "Keywords & themes"],
            horizontal=True,
            label_visibility="collapsed",
        )

    query = st.text_input(
        "Search",
        placeholder={
            "Book title": "e.g. Maus, Persepolis, A Contract with God",
            "Author": "e.g. Marjane Satrapi, Will Eisner, Alison Bechdel",
            "Keywords & themes": "e.g. memoir family war identity politics",
        }[search_mode],
        label_visibility="collapsed",
    )

    search_clicked = st.button("Search", use_container_width=True)

    if search_clicked and query:
        mode_map = {
            "Book title": "title",
            "Author": "author",
            "Keywords & themes": "keywords",
        }

        qb, sa, si, hg = recommend_three_lanes(
            query,
            df,
            tfidf_matrix,
            vectorizer,
            search_by=mode_map[search_mode],
        )

        st.session_state.query_book = qb
        st.session_state.same_author = sa
        st.session_state.similar = si
        st.session_state.hidden_gems = hg
        st.session_state.no_results = qb is None and mode_map[search_mode] != "keywords"

    query_book = st.session_state.query_book
    same_author = st.session_state.same_author
    similar = st.session_state.similar
    hidden_gems = st.session_state.hidden_gems

    if st.session_state.no_results:
        st.warning("No results found.")

    elif query_book is not None or len(similar) > 0:
        if query_book is not None:
            st.markdown(
                f"""
                <div style="background:rgba(0,0,0,0.65); padding:0.75rem 1rem;
                            border-radius:8px; margin-bottom:1.25rem; margin-top:1rem;
                            max-width:700px; margin-left:auto; margin-right:auto;">
                    <span style="color:#F5D78E; font-size:0.85rem;">Showing results for:</span><br>
                    <strong style="color:#F5F0E8; font-size:1.05rem;">
                        {safe(query_book['title'])} — {safe(query_book['author'])}
                    </strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

        def render_lane(books, border_color, show_tag=False):
            for i, (_, book) in enumerate(books.iterrows()):
                label = similarity_label(book["similarity"]) if "similarity" in book.index else ""
                rating, num = get_rating_text(book)

                year = book.get("first_publish_year", "")
                year_text = f" · {int(year)}" if pd.notna(year) and year else ""

                btn_key = f"graphic_card_{i}_{border_color[-3:]}_{str(book['title'])[:12]}"

                tag_text = "Literary / thematic match" if show_tag else ""
                right_side = f"{tag_text} · {label}" if show_tag and label else (tag_text or label)

                st.markdown(
                    f"""
                    <div style="max-width:700px; margin:0 auto;">
                        <div style="background:rgba(0,0,0,0.7); padding:1rem 1.25rem 0.5rem 1.25rem;
                                    border-radius:10px 10px 0 0; margin-bottom:0;
                                    border-left:4px solid {border_color};
                                    border-top:1px solid rgba(255,255,255,0.05);
                                    border-right:1px solid rgba(255,255,255,0.05);">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <div style="flex:1;">
                                    <strong style="color:#F5F0E8; font-size:1.05rem;">
                                        {safe(book['title'])}
                                    </strong><br>
                                    <span style="color:#D4C5A9; font-size:0.9rem;">
                                        {safe(book['author'])}
                                    </span><br>
                                    <span style="color:#D4C5A9; font-size:0.82rem;">
                                        {rating} {num} {year_text}
                                    </span>
                                </div>
                                <div style="text-align:right; padding-left:1rem; min-width:90px;
                                            color:{border_color}; font-size:0.82rem;">
                                    {safe(right_side)}
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button("📖 Description & Author Bio", key=btn_key, use_container_width=True):
                    st.session_state.selected_book = book.to_dict()

                st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

        if len(same_author) > 0:
            st.markdown(
                '<h3 style="color:#F5D78E; margin:1.25rem 0 0.5rem 0; text-align:center;">More by this author</h3>',
                unsafe_allow_html=True,
            )
            render_lane(same_author, "#F5D78E")

        st.markdown(
            '<h3 style="color:#F5D78E; margin:1.25rem 0 0.5rem 0; text-align:center;">Similar graphic novels</h3>',
            unsafe_allow_html=True,
        )
        render_lane(similar, "#A8D5B5")

        if len(hidden_gems) > 0:
            st.markdown(
                '<h3 style="color:#F5D78E; margin:1.25rem 0 0.5rem 0; text-align:center;">💎 Literary & thematic gems</h3>',
                unsafe_allow_html=True,
            )
            render_lane(hidden_gems, "#E8B4C0", show_tag=True)

        if st.session_state.selected_book is not None:
            show_book_dialog(st.session_state.selected_book)
            st.session_state.selected_book = None

        all_authors = list(
            dict.fromkeys(
                (list(same_author["author"].unique()) if len(same_author) > 0 else [])
                + (list(similar["author"].unique()) if len(similar) > 0 else [])
                + (list(hidden_gems["author"].unique()) if len(hidden_gems) > 0 else [])
            )
        )

        if all_authors:
            st.markdown(
                "<p style='color:#F5D78E; font-size:0.9rem; margin-top:1rem;'>👤 View author bio:</p>",
                unsafe_allow_html=True,
            )
            show_author_bio(all_authors, safe)

# ══ RIGHT ════════════════════════════════════════════════════════════════════
with right:
    st.markdown(
        """
        <h4 style="color:#F5D78E; text-align:center; margin-bottom:0.25rem;">
            Discover
        </h4>
        <p style="color:#D4C5A9; font-size:0.8rem; text-align:center;
                  margin-bottom:1rem;">
            Graphic novels from the collection
        </p>
        """,
        unsafe_allow_html=True,
    )

    discover_pool = df[
        (df["cover_url"].str.startswith("http", na=False))
        & (df["description"].str.len() > 150)
        & (~df["title"].str.contains(
            r"write your own|how to|guide|manual|workbook|textbook|coloring book|activity book|drawing|make comics|making comics|history of comics|theory",
            case=False,
            na=False,
            regex=True,
        ))
    ]

    if len(discover_pool) >= 5:
        discover_books = discover_pool.sample(5, random_state=None)
    else:
        discover_books = discover_pool

    covers_html = ""

    for _, book in discover_books.iterrows():
        title = safe(book["title"])[:35] + ("..." if len(str(book["title"])) > 35 else "")
        author = safe(book["author"])[:25]
        url = str(book["cover_url"])
        ol_key = str(book.get("ol_key", ""))
        source_url = f"https://openlibrary.org{ol_key}" if ol_key and ol_key != "nan" else ""
        source = "Open Library"
        

        link_start = f'<a href="{source_url}" target="_blank" style="text-decoration:none;">' if source_url else ""
        link_end = "</a>" if source_url else ""

        covers_html += f"""
            {link_start}
                <div style="background:rgba(0,0,0,0.55); padding:0.5rem;
                            border-radius:8px; margin-bottom:0.75rem;
                            border:1px solid rgba(255,255,255,0.12);
                            text-align:center;"
                     onmouseover="this.style.borderColor='rgba(245,215,142,0.5)'"
                     onmouseout="this.style.borderColor='rgba(255,255,255,0.12)'">
                    <img src="{url}"
                         style="max-height:220px; max-width:100%;
                                object-fit:contain; border-radius:3px;
                                margin-bottom:0.5rem;"
                         onerror="this.style.display='none'"/>
                    <p style="color:#F5F0E8; font-size:0.8rem; margin:0;
                               font-weight:bold; line-height:1.3;">
                        {title}
                    </p>
                    <p style="color:#D4C5A9; font-size:0.72rem; margin:0;">
                        {author}
                    </p>
                    
                </div>
            {link_end}
        """

    st.markdown(covers_html, unsafe_allow_html=True)