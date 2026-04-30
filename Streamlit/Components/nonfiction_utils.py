# nonfiction_utils.py — helper functions for the Non-Fiction page


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


