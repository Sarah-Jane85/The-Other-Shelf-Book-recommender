# ── Pages/World_Fantasy.py ──────────────────────────────────────────────────
import json
import pickle
import base64
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))
from Components.shared import set_page_style, back_button, show_author_bio, get_author_bio

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).resolve().parents[2]
MODEL_DIR = ROOT / "Models"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="World Fantasy — The Other Shelf",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

set_page_style()
back_button()

# ── Load model ────────────────────────────────────────────────────────────────
@st.cache_resource
def load_model():
    df           = pd.DataFrame(json.load(open(MODEL_DIR / "fantasy_books_index.json", encoding="utf-8")))
    tfidf_matrix = sparse.load_npz(MODEL_DIR / "fantasy_tfidf_matrix.npz")
    with open(MODEL_DIR / "fantasy_vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    return df, tfidf_matrix, vectorizer

df, tfidf_matrix, vectorizer = load_model()

# ── Heritage region mapping ───────────────────────────────────────────────────
HERITAGE_REGIONS = {
    "🌍 Africa & Diaspora": ["africa", "african-fantasy", "african-science-fiction",
                              "afrofuturism", "anansi", "igbo", "orisha", "yoruba", "zulu"],
    "⛩️ Asia":              ["asian-fantasy", "asian-science-fiction", "chinese",
                              "japanese", "korean", "wuxia", "xianxia"],
    "🌺 South Asia":        ["south_asian"],
    "🌊 Oceania":           ["oceania", "australian-fantasy"],
    "🕌 Middle East":       ["middle-eastern-fantasy", "middle_eastern"],
    "🌿 Indigenous":        ["indigenous-fantasy", "indigenous_americas"],
    "🌎 Latin America":     ["latin-american-fantasy", "latin_american",
                              "south-american-fantasy"],
    "🌐 Southeast Asia":    ["filipino", "southeast_asian"],
}

# Reverse lookup: tag → region name
TAG_TO_REGION = {}
for region, tags in HERITAGE_REGIONS.items():
    for tag in tags:
        TAG_TO_REGION[tag] = region

UNDERREPRESENTED = {
    "oceania", "australian-fantasy", "indigenous-fantasy", "indigenous_americas",
    "latin-american-fantasy", "latin_american", "south-american-fantasy",
    "middle-eastern-fantasy", "middle_eastern", "filipino", "southeast_asian",
    "african-science-fiction", "orisha", "igbo", "akan", "zulu", "yoruba",
    "anansi", "xianxia", "wuxia",
}

# ── Helper: get region for a book ────────────────────────────────────────────
def get_region(source_tag):
    """Return the human-readable region for a source_tag value."""
    if isinstance(source_tag, list):
        for t in source_tag:
            if t in TAG_TO_REGION:
                return TAG_TO_REGION[t]
    elif isinstance(source_tag, str) and source_tag in TAG_TO_REGION:
        return TAG_TO_REGION[source_tag]
    return None

def tags_in_region(source_tag, region_tags):
    """Return True if any of the book's source tags are in the given region tags list."""
    if isinstance(source_tag, list):
        return any(t in region_tags for t in source_tag)
    return source_tag in region_tags

# ── Helper functions ──────────────────────────────────────────────────────────
def safe(text):
    if pd.isna(text): return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def similarity_label(score):
    if score >= 0.3:  return "Almost identical"
    if score >= 0.15: return "Very similar"
    if score >= 0.08: return "Similar"
    if score >= 0.04: return "Loosely related"
    return "Inspired by"

# ── Book detail dialog ────────────────────────────────────────────────────────
@st.dialog("Book Details", width="large")
def show_book_dialog(book):
    title  = safe(book.get("title", ""))
    author = safe(book.get("author", ""))

    st.markdown(f"""
        <h2 style="color:#F5D78E; margin:0 0 0.25rem 0;">{title}</h2>
        <p style="color:#D4C5A9; font-size:1rem; margin:0 0 1rem 0;">by {author}</p>
    """, unsafe_allow_html=True)

    rating = f"⭐ {book['avg_rating']}" if pd.notna(book.get('avg_rating')) else ""
    num    = f"· {int(book['num_ratings']):,} ratings" if pd.notna(book.get('num_ratings')) and book.get('num_ratings', 0) > 0 else ""
    tag    = safe(str(book.get("source_tag", "")))
    region = get_region(book.get("source_tag", ""))

    st.markdown(f"""
        <p style="color:#D4C5A9; font-size:0.9rem;">
            {rating} {num} &nbsp;·&nbsp;
            <span style="color:#F5D78E;">{region or tag}</span>
        </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2 = st.tabs(["📖 Description", "👤 Author Bio"])

    with tab1:
        desc = book.get("description", "")
        if desc and "A work of fantasy fiction involving" not in str(desc):
            st.markdown(f"""
                <p style="color:#F5F0E8; font-size:1rem; line-height:1.8;">
                    {safe(str(desc))}
                </p>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#D4C5A9;'>No description available.</p>",
                        unsafe_allow_html=True)
        if book.get("source_url"):
            st.markdown(f"[View on {book.get('source', 'source')} →]({book['source_url']})")

    with tab2:
        bio = get_author_bio(book.get("author", ""))
        if bio and bio["extract"]:
            col_text, col_img = st.columns([3, 1])
            with col_text:
                st.markdown(f"""
                    <p style="color:#F5F0E8; font-size:0.95rem; line-height:1.8;">
                        {safe(bio['extract'][:600])}...
                    </p>
                    <a href="{bio['url']}" target="_blank"
                       style="color:#A8D5B5; font-size:0.85rem;">
                        Read more on Wikipedia →
                    </a>
                """, unsafe_allow_html=True)
            with col_img:
                if bio["image"]:
                    st.image(bio["image"], width=130)
        else:
            st.markdown(
                f"<p style='color:#D4C5A9;'>No bio found for {safe(book.get('author', ''))}.</p>",
                unsafe_allow_html=True
            )

# ── Recommender ───────────────────────────────────────────────────────────────
def recommend_three_lanes(idx, query_book, df, tfidf_matrix, vectorizer,
                          query_vec=None, top_n=5):
    """
    Returns same_author, similar, hidden_gems, cross_cultural DataFrames.
    query_vec is used for keyword mode (idx=None).
    """
    if query_vec is None:
        query_vec = tfidf_matrix[idx]

    sim_scores            = cosine_similarity(query_vec, tfidf_matrix).flatten()
    results               = df.copy()
    results["similarity"] = sim_scores
    if idx is not None:
        results = results.drop(index=idx)

    query_author = query_book["author"].lower().strip() if query_book is not None else ""

    same_author = results[
        results["author"].str.lower().str.strip() == query_author
    ].sort_values("similarity", ascending=False).head(top_n) if query_author else pd.DataFrame()

    similar = results[
        results["author"].str.lower().str.strip() != query_author
    ].sort_values("similarity", ascending=False).head(top_n)

    # ── Hidden gems — from underrepresented regions ───────────────────────
    hidden_pool = results[
        (results["source_tag"].apply(lambda t: tags_in_region(t, UNDERREPRESENTED))) &
        (results["author"].str.lower().str.strip() != query_author) &
        (results["similarity"] >= 0.02)
    ]
    hidden_gems = (
        hidden_pool
        .sort_values("similarity", ascending=False)
        .head(top_n)
    )

    # ── Cross-cultural — similar content, different heritage region ───────
    cross_cultural = pd.DataFrame()
    if query_book is not None:
        query_region_tags = []
        q_tag = query_book.get("source_tag", "")
        if isinstance(q_tag, list):
            query_region_tags = q_tag
        elif q_tag:
            query_region_tags = [q_tag]

        # Find which named region the query book belongs to
        query_named_region = get_region(q_tag)

        # Get all tags that belong to the same named region (to exclude them)
        same_region_tags = set()
        if query_named_region and query_named_region in HERITAGE_REGIONS:
            same_region_tags = set(HERITAGE_REGIONS[query_named_region])

        cross_pool = results[
            (results["author"].str.lower().str.strip() != query_author) &
            (results["similarity"] >= 0.04) &
            # Exclude books from the same heritage region
            (~results["source_tag"].apply(lambda t: tags_in_region(t, same_region_tags)))
        ]

        # Get one representative per region for variety
        cross_pool = cross_pool.copy()
        cross_pool["region"] = cross_pool["source_tag"].apply(get_region)
        cross_cultural = (
            cross_pool[cross_pool["region"].notna()]
            .sort_values("similarity", ascending=False)
            .groupby("region").first()
            .reset_index()
            .sort_values("similarity", ascending=False)
            .head(top_n)
        )

    return same_author, similar, hidden_gems, cross_cultural


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="text-align:center; padding:1.5rem 0 1rem 0;">
        <h1 style="font-size:3.5rem; color:#F5F0E8;
                   text-shadow:2px 2px 8px rgba(0,0,0,0.8);">
            World Fantasy
        </h1>
        <p style="font-size:1.8rem; color:#D4C5A9; margin-bottom:0.75rem;">
            Fantasy &amp; science fiction rooted in non-western mythologies and folklore
        </p>
        <p style="font-size:1.3rem; color:#F5F0E8; max-width:700px;
                  margin:0 auto; line-height:1.8;
                  background:rgba(0,0,0,0.5); padding:1rem 1.5rem;
                  border-radius:10px;">
            Everyone reads the same 10 books. This recommender helps you find
            something amazing from a different heritage — African mythology,
            Japanese folklore, Andean gods, Indigenous dreamtime, Arabian djinn
            and much more.
            <strong style="color:#F5D78E;">about 3250 books</strong>
            from traditions beyond the western canon. Broaden your horizon.
        </p>
        <p style="color:#D4C5A9; font-size:1.2rem; margin-top:0.75rem;">
            🌍 Africa &nbsp;·&nbsp; ⛩️ Asia &nbsp;·&nbsp; 🕌 Middle East
            &nbsp;·&nbsp; 🌿 Indigenous &nbsp;·&nbsp; 🌊 Oceania
            &nbsp;·&nbsp; 🌺 South Asia &nbsp;·&nbsp; 🌎 Latin America
        </p>
    </div>
    <hr style="border-color:rgba(255,255,255,0.15); margin-bottom:1.5rem;">
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
middle, spacer, right = st.columns([4, 0.5, 1])

# ── Session state ─────────────────────────────────────────────────────────────
for key, default in [
    ("query_book",     None),
    ("same_author",    pd.DataFrame()),
    ("similar",        pd.DataFrame()),
    ("hidden_gems",    pd.DataFrame()),
    ("cross_cultural", pd.DataFrame()),
    ("no_results",     False),
    ("selected_book",  None),
    ("title_matches",  pd.DataFrame()),   # NEW: for partial title pick list
    ("last_query",     ""),
    ("heritage_filter", "All heritages"), # NEW: heritage filter
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ══ MIDDLE ════════════════════════════════════════════════════════════════════
with middle:
    st.markdown("""
    <style>
        div[data-testid="stButton"] { max-width: 700px; margin: 0 auto; }
        div[data-testid="stTextInput"] { max-width: 700px; margin: 0 auto; }
        div[data-testid="stRadio"] { max-width: 700px; margin: 0 auto; }
        div[data-testid="stHorizontalBlock"] { max-width: 700px; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

    # ── Search mode radio ─────────────────────────────────────────────────
    col_l, col_radio, col_r = st.columns([0.8, 5.4, 0.8])
    with col_radio:
        search_mode = st.radio(
            "Search by:",
            ["Book title", "Author", "Keywords & themes"],
            horizontal=True,
            label_visibility="collapsed"
        )

    # ── Heritage filter (only for Book title / Author modes) ─────────────
    heritage_options = ["All heritages"] + list(HERITAGE_REGIONS.keys())
    if search_mode != "Keywords & themes":
        st.markdown("""
        <style>
            div[data-testid="stSelectbox"] { 
                max-width: 700px; 
                margin: 0 auto;
                display: block;
            }
            div[data-testid="stSelectbox"] > div {
                max-width: 700px;
            }
        </style>
        """, unsafe_allow_html=True)
        st.session_state.heritage_filter = st.selectbox(
            "Filter by heritage:",
            heritage_options,
            index=heritage_options.index(st.session_state.heritage_filter),
            label_visibility="collapsed",
        )
    else:
        st.session_state.heritage_filter = "All heritages"

    # ── Text input ────────────────────────────────────────────────────────
    query = st.text_input(
        "Search",
        placeholder={
            "Book title":        "e.g. Children of Blood and Bone",
            "Author":            "e.g. Nnedi Okorafor",
            "Keywords & themes": "e.g. japanese spirit world fox magic",
        }[search_mode],
        label_visibility="collapsed",
        key="search_input"
    )

    search_clicked = st.button("Search", use_container_width=True)

    do_search = search_clicked or (
        query != "" and query != st.session_state.get("last_query", "")
    )

    if do_search and query:
        st.session_state.last_query     = query
        st.session_state.title_matches  = pd.DataFrame()
        st.session_state.no_results     = False

        mode_map = {
            "Book title":        "title",
            "Author":            "author",
            "Keywords & themes": "keywords",
        }
        mode = mode_map[search_mode]

        # ── Apply heritage filter to search pool ──────────────────────────
        search_df = df.copy()
        chosen_heritage = st.session_state.heritage_filter
        if chosen_heritage != "All heritages":
            region_tags = HERITAGE_REGIONS[chosen_heritage]
            search_df = search_df[
                search_df["source_tag"].apply(lambda t: tags_in_region(t, region_tags))
            ]

        if mode == "keywords":
            query_vec  = vectorizer.transform([query])
            sa, si, hg, cc = recommend_three_lanes(
                None, None, search_df, tfidf_matrix, vectorizer,
                query_vec=query_vec
            )
            st.session_state.query_book     = None
            st.session_state.same_author    = sa
            st.session_state.similar        = si
            st.session_state.hidden_gems    = hg
            st.session_state.cross_cultural = cc

        else:
            col = "title" if mode == "title" else "author"
            matches = search_df[search_df[col].str.contains(query, case=False, na=False)]

            if len(matches) == 0:
                st.session_state.no_results = True

            elif len(matches) == 1 or mode == "author":
                # Single match or author search → go straight to results
                idx        = matches.index[0]
                query_book = df.iloc[idx]
                sa, si, hg, cc = recommend_three_lanes(
                    idx, query_book, df, tfidf_matrix, vectorizer
                )
                st.session_state.query_book     = query_book
                st.session_state.same_author    = sa
                st.session_state.similar        = si
                st.session_state.hidden_gems    = hg
                st.session_state.cross_cultural = cc

            else:
                # Multiple title matches → show pick list
                st.session_state.title_matches = matches.reset_index()

    # ── If multiple title matches: show pick list ─────────────────────────
    if not st.session_state.title_matches.empty:
        matches = st.session_state.title_matches
        st.markdown(f"""
            <div style="background:rgba(0,0,0,0.65); padding:0.75rem 1rem;
                        border-radius:8px; margin-bottom:1rem; margin-top:1rem;
                        max-width:700px; margin-left:auto; margin-right:auto;">
                <span style="color:#F5D78E; font-size:0.9rem;">
                    📚 {len(matches)} books found — which one did you mean?
                </span>
            </div>
        """, unsafe_allow_html=True)

        options = [
            f"{row['title']} — {row['author']}"
            for _, row in matches.iterrows()
        ]

        col_l3, col_pick, col_r3 = st.columns([1.6, 3.8, 1.6])
        with col_pick:
            chosen = st.selectbox(
                "Pick a book:",
                ["— select a book —"] + options,
                label_visibility="collapsed",
                key="title_pick"
            )

        if chosen != "— select a book —":
            chosen_idx_in_matches = options.index(chosen)
            idx        = int(matches.iloc[chosen_idx_in_matches]["index"])
            query_book = df.iloc[idx]
            sa, si, hg, cc = recommend_three_lanes(
                idx, query_book, df, tfidf_matrix, vectorizer
            )
            st.session_state.query_book     = query_book
            st.session_state.same_author    = sa
            st.session_state.similar        = si
            st.session_state.hidden_gems    = hg
            st.session_state.cross_cultural = cc
            st.session_state.title_matches  = pd.DataFrame()  # clear the list
            st.rerun()

    # ── Show results ──────────────────────────────────────────────────────
    query_book    = st.session_state.query_book
    same_author   = st.session_state.same_author
    similar       = st.session_state.similar
    hidden_gems   = st.session_state.hidden_gems
    cross_cultural = st.session_state.cross_cultural

    if st.session_state.no_results:
        st.warning("No results found. Try a different title or remove the heritage filter.")

    elif query_book is not None or len(similar) > 0:

        if query_book is not None:
            region = get_region(query_book.get("source_tag", ""))
            st.markdown(f"""
                <div style="background:rgba(0,0,0,0.65); padding:0.75rem 1rem;
                            border-radius:8px; margin-bottom:1.25rem; margin-top:1rem;
                            max-width:700px; margin-left:auto; margin-right:auto;">
                    <span style="color:#F5D78E; font-size:0.85rem;">Showing results for:</span><br>
                    <strong style="color:#F5F0E8; font-size:1.05rem;">
                        {safe(query_book['title'])} — {safe(query_book['author'])}
                    </strong>
                    {"<br><span style='color:#D4C5A9; font-size:0.85rem;'>" + region + "</span>" if region else ""}
                </div>
            """, unsafe_allow_html=True)

        # ── Render cards ──────────────────────────────────────────────────
        def render_lane(books, border_color, show_tag=False):
            for i, (_, book) in enumerate(books.iterrows()):
                label    = similarity_label(book["similarity"]) if "similarity" in book.index else ""
                r        = f"⭐ {book['avg_rating']}" if pd.notna(book.get("avg_rating")) else ""
                n        = f"· {int(book['num_ratings']):,} ratings" if pd.notna(book.get("num_ratings")) and book.get("num_ratings", 0) > 0 else ""
                btn_key  = f"card_{i}_{border_color[-3:]}_{safe(book['title'])[:8]}"

                if show_tag:
                    region_name = book.get("region") or get_region(book.get("source_tag", ""))
                    right_text  = f"{safe(str(region_name))} · {label}" if region_name else label
                else:
                    right_text = label

                st.markdown(f"""
                    <div style="max-width:900px; margin:0 auto;">
                        <div style="background:rgba(0,0,0,0.7); padding:1rem 1.25rem 0.5rem 1.25rem;
                                    border-radius:10px 10px 0 0; margin-bottom:0;
                                    border-left:4px solid {border_color};
                                    border-top:1px solid rgba(255,255,255,0.05);
                                    border-right:1px solid rgba(255,255,255,0.05);">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                                <div style="flex:1;">
                                    <strong style="color:#F5F0E8; font-size:1.05rem;">{safe(book['title'])}</strong><br>
                                    <span style="color:#D4C5A9; font-size:0.9rem;">{safe(book['author'])}</span><br>
                                    <span style="color:#D4C5A9; font-size:0.82rem;">{r} {n}</span>
                                </div>
                                <div style="text-align:right; padding-left:1rem; min-width:100px;
                                            color:{border_color}; font-size:0.82rem;">
                                    {right_text}
                                </div>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if st.button("📖 Description & Author Bio", key=btn_key, use_container_width=True):
                    st.session_state.selected_book = book.to_dict()

                st.markdown("<div style='margin-bottom:0.6rem;'></div>", unsafe_allow_html=True)

        # ── Lane 1: More by this author ───────────────────────────────────
        if len(same_author) > 0:
            st.markdown("<h3 style=\"color:#F5D78E; margin:1.25rem 0 0.5rem 0; text-align:center;\">More by this author</h3>",
                unsafe_allow_html=True)
            render_lane(same_author, "#F5D78E")

        # ── Lane 2: Similar books ─────────────────────────────────────────
        st.markdown("<h3 style=\"color:#F5D78E; margin:1.25rem 0 0.5rem 0; text-align:center;\">Similar books</h3>",
            unsafe_allow_html=True)
        render_lane(similar, "#A8D5B5")

        # ── Lane 3: Hidden gems ───────────────────────────────────────────
        if len(hidden_gems) > 0:
            st.markdown("<h3 style=\"color:#F5D78E; margin:1.25rem 0 0.5rem 0; text-align:center;\">💎 Hidden gems from underrepresented heritages</h3>",
                unsafe_allow_html=True)
            render_lane(hidden_gems, "#E8B4C0", show_tag=True)

        # ── Lane 4: Cross-cultural recommendations ────────────────────────
        if len(cross_cultural) > 0:
            st.markdown("<h3 style=\"color:#F5D78E; margin:1.25rem 0 0.5rem 0; text-align:center;\">🌐 Same story, different world</h3>",
                unsafe_allow_html=True)
            st.markdown("""
                <p style="color:#D4C5A9; font-size:0.9rem; text-align:center;
                           max-width:700px; margin:0 auto 0.75rem auto;">
                    You liked this story — here's the same kind of magic from a completely different part of the world.
                </p>
            """, unsafe_allow_html=True)
            render_lane(cross_cultural, "#B4C8E8", show_tag=True)

        # ── Show dialog ───────────────────────────────────────────────────
        if st.session_state.selected_book is not None:
            show_book_dialog(st.session_state.selected_book)
            st.session_state.selected_book = None

        # ── Author bio ────────────────────────────────────────────────────
        all_authors = list(dict.fromkeys(
            (list(same_author["author"].unique()) if len(same_author) > 0 else []) +
            list(similar["author"].unique()) +
            (list(hidden_gems["author"].unique()) if len(hidden_gems) > 0 else []) +
            (list(cross_cultural["author"].unique()) if len(cross_cultural) > 0 else [])
        ))
    

# ══ RIGHT ═════════════════════════════════════════════════════════════════════
with right:
    st.markdown("""
        <h4 style="color:#F5D78E; text-align:center; margin-bottom:0.25rem;">
            Discover
        </h4>
        <p style="color:#D4C5A9; font-size:0.8rem; text-align:center;
                  margin-bottom:1rem;">
            Gems from our collection
        </p>
    """, unsafe_allow_html=True)

    obscure = df[
        (df["num_ratings"] < 500) &
        (df["num_ratings"] > 0) &
        (df["cover_url"].str.startswith("http", na=False)) &
        (df["description"].str.len() > 200) &
        (~df["description"].str.contains("A work of fantasy fiction involving", na=False)) &
        (~df["title"].str.contains(r"#\d|Vol\.|Volume|Season One|Season Two",
                                case=False, na=False, regex=True))
    ].sample(5, random_state=None)

    covers_html = ""
    for _, book in obscure.iterrows():
        title      = safe(book['title'])[:35] + ('...' if len(str(book['title'])) > 35 else '')
        author     = safe(book['author'])[:25]
        url        = str(book['cover_url'])
        source_url = str(book.get('source_url', ''))
        source     = str(book.get('source', 'source')).replace('_', ' ')

        covers_html += f"""
            <a href="{source_url}" target="_blank" style="text-decoration:none;">
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
                    <p style="color:#F5D78E; font-size:0.68rem; margin:0.2rem 0 0 0;">
                        view on {source} →
                    </p>
                </div>
            </a>"""

    st.markdown(covers_html, unsafe_allow_html=True)
