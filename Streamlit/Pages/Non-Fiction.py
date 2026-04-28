import sys
from pathlib import Path
import html
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parent.parent))
from Src.recommender_non_fiction import build_index, load_data, recommend
from Components.shared import set_page_style, show_author_bio, back_button
from Components.nonfiction_utils import get_cover_url, get_goodreads_url, render_book_cover


st.set_page_config(page_title="Book Recommender", page_icon="📚", layout="wide")
set_page_style()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
    <div style="text-align:center; padding:1.5rem 0 1rem 0;">
        <h1 style="font-size:3rem; color:#F5F0E8;
                   text-shadow:2px 2px 8px rgba(0,0,0,0.8);">
            📚 Book Recommender
        </h1>
        <p style="font-size:1.05rem; color:#D4C5A9; margin-bottom:0.75rem;">
            Non-Fiction & Alternative Perspectives
        </p>
        <p style="font-size:1rem; color:#F5F0E8; max-width:700px;
                  margin:0 auto; line-height:1.8;
                  background:rgba(0,0,0,0.5); padding:1rem 1.5rem;
                  border-radius:10px;">
            Search by keyword, topic, author, or title — we'll find the closest matches
            in our collection of left-wing thought and alternative perspectives.
            <strong style="color:#F5D78E;">3,034 books</strong>
            from critical theory, postcolonial studies, and radical perspectives.
        </p>
    </div>
    <hr style="border-color:rgba(255,255,255,0.15); margin-bottom:1.5rem;">
""", unsafe_allow_html=True)

back_button()

# Improve text input visibility
st.markdown("""
    <style>
        .stTextInput > div > div > input {
            background-color: rgba(100,100,100,0.5) !important;
            color: #F5F0E8 !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: rgba(245,240,232,0.7) !important;
        }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def get_data():
    return load_data()


@st.cache_resource
def get_index(_df):
    return build_index(_df)


df = get_data()
vectorizer, matrix = get_index(df)

query = st.text_input(
    "What are you looking for?",
    placeholder="e.g. capitalism, colonialism, David Harvey, Capital...",
)
top_n = st.slider("Number of results", min_value=3, max_value=20, value=10)

if query.strip():
    results = recommend(query, df, vectorizer, matrix, top_n=top_n)

    if results.empty:
        st.info("No matches found. Try different keywords.")
    else:
        st.markdown(f"**{len(results)} results** for *{query}*")
        st.divider()

        for _, row in results.iterrows():
            year = f" · {int(row['year_published'])}" if pd.notna(row["year_published"]) else ""
            
            cover_url = get_cover_url(row['title'], row['author'])
            col1, col2 = st.columns([1, 4])

            render_book_cover(col1, cover_url)

            with col2:
                st.markdown(f"### {row['title']}")
                st.markdown(f"**{row['author']}**{year}")

                goodreads_url = get_goodreads_url(str(row.get('open_library_key', '')))
                if goodreads_url:
                    st.markdown(f"[📖 View on Goodreads]({goodreads_url})")

                with st.expander("Description"):
                    st.write(row["description"])
            
            st.divider()
        
        st.markdown("### 📖 Learn More About the Authors")
        authors = results['author'].unique().tolist()
        show_author_bio(authors, html.escape)
