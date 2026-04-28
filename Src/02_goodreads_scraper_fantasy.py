"""
02_goodreads_scraper_fantasy.py
────────────────────────────────
Scrapes non-western fantasy books from Goodreads community shelves
using Selenium for pagination and description fetching.

Requires manual Goodreads login in the browser window before scraping.
Credentials can also be provided via .env file for automatic login.

Usage:
    python 02_goodreads_scraper_fantasy.py

Output:
    Data/Raw/non_western_fantasy/goodreads_with_descriptions.csv
"""

import os
import re
import time
import pandas as pd
from pathlib import Path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT   = Path(__file__).resolve().parents[2]
RAW_DIR     = REPO_ROOT / "Data" / "Raw" / "non_western_fantasy"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = RAW_DIR / "goodreads_raw.csv"
DESC_OUTPUT = RAW_DIR / "goodreads_with_descriptions.csv"
DESC_CKPT   = RAW_DIR / "goodreads_desc_checkpoint.csv"

# ── Config ────────────────────────────────────────────────────────────────────
DELAY      = 3.0   # seconds between shelf pages
DESC_DELAY = 2.0   # seconds between description fetches
SAVE_EVERY = 50    # checkpoint frequency

SHELVES = [
    "african-fantasy",
    "asian-fantasy",
    "indigenous-fantasy",
    "south-american-fantasy",
    "australian-fantasy",
    "middle-eastern-fantasy",
    "latin-american-fantasy",
    "afrofuturism",
    "african-science-fiction",
    "asian-science-fiction",
]


# ── Browser setup ─────────────────────────────────────────────────────────────
def create_driver() -> webdriver.Chrome:
    """Create a Chrome WebDriver with anti-detection settings."""
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# ── Parsing functions ─────────────────────────────────────────────────────────
def parse_shelf_page(page_source: str, shelf: str) -> list[dict]:
    """Parse all books from a Goodreads shelf page."""
    soup    = BeautifulSoup(page_source, "html.parser")
    records = []

    for div in soup.select("div.elementList"):
        title_tag  = div.select_one("a.bookTitle")
        author_tag = div.select_one("span[itemprop='name']")
        grey_tag   = div.select_one("span.greyText.smallText")
        cover_tag  = div.select_one("img")

        if not title_tag:
            continue

        title     = title_tag.get_text(strip=True)
        href      = title_tag["href"].split("?")[0]
        author    = author_tag.get_text(strip=True) if author_tag else ""
        grey_text = grey_tag.get_text(strip=True) if grey_tag else ""

        rating_m     = re.search(r'avg rating ([\d.]+)', grey_text)
        num_rating_m = re.search(r'([\d,]+)\s+ratings', grey_text)
        year_m       = re.search(r'published (\d{4})', grey_text)
        cover_url    = cover_tag["src"] if cover_tag and cover_tag.get("src") else ""

        records.append({
            "title":          title,
            "author":         author,
            "goodreads_url":  f"https://www.goodreads.com{href}",
            "cover_url":      cover_url,
            "avg_rating":     float(rating_m.group(1)) if rating_m else None,
            "num_ratings":    int(num_rating_m.group(1).replace(",", "")) if num_rating_m else None,
            "year_published": int(year_m.group(1)) if year_m else None,
            "shelf":          shelf,
        })

    return records


def fetch_description(driver: webdriver.Chrome, goodreads_url: str) -> str:
    """Fetch the description for a single book from its Goodreads page."""
    driver.get(goodreads_url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    desc = soup.select_one("div[data-testid='description'] span.Formatted")
    if not desc:
        desc = soup.select_one("#description span")
    if not desc:
        desc = soup.select_one("span.Formatted")

    return desc.get_text(separator=" ", strip=True) if desc else ""


# ── Scraping functions ────────────────────────────────────────────────────────
def scrape_shelf(driver: webdriver.Chrome, shelf: str, max_pages: int = 20) -> list[dict]:
    """Scrape all pages of a Goodreads shelf."""
    all_records = []
    driver.get(f"https://www.goodreads.com/shelf/show/{shelf}")
    time.sleep(3)
    page = 1

    while page <= max_pages:
        records = parse_shelf_page(driver.page_source, shelf)

        if not records:
            print(f"  No books on page {page} — stopping")
            break

        all_records.extend(records)
        print(f"  Page {page}: {len(records)} books (total: {len(all_records)})")

        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, "a.next_page")
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(DELAY)
            page += 1
        except Exception:
            print(f"  No more pages")
            break

    return all_records


def login(driver: webdriver.Chrome) -> bool:
    """Attempt automatic login with credentials from .env file."""
    email    = os.getenv("GOODREADS_EMAIL", "")
    password = os.getenv("GOODREADS_PASSWORD", "")

    if not email or not password:
        print("⚠️  No credentials found in .env — please log in manually")
        driver.get("https://www.goodreads.com/user/sign_in")
        input("Press Enter after logging in manually...")
        return True

    wait = WebDriverWait(driver, 20)
    driver.get("https://www.goodreads.com/user/sign_in")
    time.sleep(3)

    try:
        email_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Sign in with email')]"))
        )
        email_btn.click()
        time.sleep(2)

        wait.until(EC.presence_of_element_located((By.ID, "user_email"))).send_keys(email)
        driver.find_element(By.ID, "user_password").send_keys(password)
        driver.find_element(By.NAME, "next").click()
        time.sleep(3)

        if "sign_in" not in driver.current_url:
            print("✅ Login successful")
            return True
        else:
            print("⚠️  Login failed — please log in manually")
            input("Press Enter after logging in manually...")
            return True

    except Exception as e:
        print(f"❌ Login error: {e}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    driver = create_driver()

    try:
        login(driver)

        # ── Phase 1: Scrape shelf listings ────────────────────────────────────
        all_records = []
        for shelf in SHELVES:
            print(f"\n── Shelf: {shelf} ──")
            try:
                records = scrape_shelf(driver, shelf, max_pages=20)
                print(f"   ✅ {len(records)} books")
                all_records.extend(records)
            except Exception as e:
                print(f"   ❌ Failed: {e}")
            time.sleep(DELAY)

        df = pd.DataFrame(all_records)
        df = df.drop_duplicates(subset=["title", "author"]).reset_index(drop=True)
        df.to_csv(OUTPUT_PATH, index=False)
        print(f"\n✅ Shelf scraping complete — {len(df):,} books saved to {OUTPUT_PATH}")

        # ── Phase 2: Description enrichment ──────────────────────────────────
        if DESC_CKPT.exists():
            df_desc   = pd.read_csv(DESC_CKPT)
            done_urls = set(df_desc.loc[
                df_desc["description"].notna() & (df_desc["description"] != ""),
                "goodreads_url"
            ])
            print(f"\nResuming descriptions — {len(done_urls):,} already done")
        else:
            df_desc           = df.copy()
            df_desc["description"] = ""
            done_urls         = set()

        todo = df_desc[~df_desc["goodreads_url"].isin(done_urls)]
        print(f"Fetching descriptions for {len(todo):,} books...")

        for i, (idx, row) in enumerate(todo.iterrows(), 1):
            try:
                desc = fetch_description(driver, row["goodreads_url"])
                df_desc.at[idx, "description"] = desc
                status = "✅" if desc else "⚠️"
            except Exception:
                df_desc.at[idx, "description"] = ""
                status = "❌"

            if i % 10 == 0:
                print(f"  [{i}/{len(todo)}] {status} {row['title'][:40]}")
            if i % SAVE_EVERY == 0:
                df_desc.to_csv(DESC_CKPT, index=False)

            time.sleep(DESC_DELAY)

        df_desc.to_csv(DESC_OUTPUT, index=False)
        print(f"\n✅ Done — {len(df_desc):,} books with descriptions")
        print(f"   Has description: {(df_desc['description'] != '').sum():,}")
        print(f"   Saved to {DESC_OUTPUT}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
