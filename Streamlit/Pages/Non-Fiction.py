import sys
from pathlib import Path
import html
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parent.parent))
from Src.recommender_non_fiction import build_index, load_data, recommend
from Components.shared import set_page_style, show_author_bio, back_button
from Components.nonfiction_utils import get_goodreads_url


st.set_page_config(page_title="Book Recommender", page_icon="📚", layout="wide")
set_page_style()
back_button()

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
            goodreads_url = get_goodreads_url(str(row.get('open_library_key', '')))
            goodreads_html = (
                f'<a href="{goodreads_url}" target="_blank" '
                f'style="color:#F5D78E; font-size:0.9rem; text-decoration:none;">'
                f'📖 View on Goodreads</a>'
                if goodreads_url else ""
            )

            st.markdown(f"""
                <div style="
                    background: rgba(20, 12, 6, 0.85);
                    border: 1px solid rgba(245, 215, 142, 0.2);
                    border-left: 3px solid #F5D78E;
                    border-radius: 10px;
                    padding: 1.1rem 1.5rem 1rem 1.5rem;
                    margin-bottom: 0.2rem;
                ">
                    <div style="font-size:1.2rem; font-weight:700; color:#F5F0E8;
                                line-height:1.4; margin-bottom:0.35rem;">
                        {html.escape(row['title'])}
                    </div>
                    <div style="color:#F5D78E; font-size:0.95rem; margin-bottom:0.6rem;">
                        {html.escape(row['author'])}{year}
                    </div>
                    {goodreads_html}
                </div>
            """, unsafe_allow_html=True)

            with st.expander("Description"):
                st.write(row["description"])

            st.markdown("<div style='margin-bottom:0.75rem;'></div>", unsafe_allow_html=True)
        
        st.markdown("### 📖 Learn More About the Authors")
        authors = results['author'].unique().tolist()
        show_author_bio(authors, html.escape)
