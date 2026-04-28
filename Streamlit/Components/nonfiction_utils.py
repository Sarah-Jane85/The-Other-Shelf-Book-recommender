# nonfiction_utils.py — helper functions for the Non-Fiction page
import requests
import streamlit as st


@st.cache_data(ttl=3600)
def get_cover_url(title: str, author: str) -> str | None:
    """
    Fetch a book cover URL from the Open Library API.

    Tries cover_i first (numeric cover ID), then falls back to ISBN.
    Returns None if no cover is found or the request fails — the page
    will show a 'Cover not found' placeholder instead.

    Results are cached for 1 hour so repeated searches don't hammer the API.
    """
    try:
        response = requests.get(
            "https://openlibrary.org/search.json",
            params={"q": f"{title} {author}", "limit": 1},
            timeout=5,
        )
        response.raise_for_status()
        docs = response.json().get("docs", [])

        if not docs:
            return None

        doc = docs[0]

        # Prefer the numeric cover ID — faster and more reliable
        if "cover_i" in doc:
            url = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg"
        elif doc.get("isbn"):
            url = f"https://covers.openlibrary.org/b/isbn/{doc['isbn'][0]}-M.jpg"
        else:
            return None

        # Quick HEAD check — avoids showing a broken image in the UI
        if requests.head(url, timeout=2).status_code == 200:
            return url

        return None

    except Exception:
        return None


def get_goodreads_url(open_library_key: str) -> str | None:
    """
    Extract a Goodreads URL from an Open Library key.

    Open Library keys that point to Goodreads use the format:
        /book/show/<ID>.<slug>
    Returns the full Goodreads URL, or None if the key doesn't match
    that format.
    """
    if not open_library_key or "/book/show/" not in open_library_key:
        return None
    try:
        goodreads_id = open_library_key.split("/book/show/")[1].split(".")[0]
        return f"https://www.goodreads.com/book/show/{goodreads_id}"
    except (IndexError, AttributeError):
        return None


def render_book_cover(col, cover_url: str | None) -> None:
    """
    Render a book cover image — or a 'Cover not found' placeholder — into
    the given Streamlit column.
    """
    with col:
        if cover_url:
            st.image(cover_url, width=100, caption="")
        else:
            st.markdown(
                """
                <div style="width:100px; height:150px;
                            background:rgba(255,255,255,0.05);
                            border:1px solid rgba(255,255,255,0.15);
                            border-radius:4px;
                            display:flex; align-items:center;
                            justify-content:center; text-align:center;
                            color:#888; font-size:0.75rem; padding:8px;">
                    Cover not found
                </div>
                """,
                unsafe_allow_html=True,
            )
