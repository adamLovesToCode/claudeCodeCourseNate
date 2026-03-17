"""
Tool: scrape_job_listings.py
Purpose: Scrape job listing pages and individual job detail pages using Firecrawl.
Output: .tmp/raw_jobs.json — list of {url, markdown, error} dicts.
"""

import json
import os
import re
import time

from dotenv import load_dotenv
import firecrawl

load_dotenv()

BASE_URL = "https://dailyremote.com/"
SEARCH_PARAMS = "search=react%20developer"
MAX_PAGES = 2
OUTPUT_PATH = ".tmp/raw_jobs.json"
DELAY_SECONDS = 1.5


def scrape_listing_page(app, page: int) -> list[str]:
    """Scrape one listing page and return a list of job detail URLs."""
    url = f"{BASE_URL}?{SEARCH_PARAMS}&page={page}"
    print(f"  Scraping listing page {page}: {url}")

    try:
        result = app.scrape(url, formats=["markdown", "links"])
        if not result:
            print(f"  [WARN] Empty result for listing page {page}")
            return []

        # Try extracting from links format first
        job_urls = []
        links = getattr(result, "links", None) or result.get("links", []) if hasattr(result, "get") else []
        if links:
            job_urls = [
                link for link in links
                if "/remote-job/" in link and "dailyremote.com" in link
            ]

        # Fallback: parse markdown for job URLs
        markdown = getattr(result, "markdown", None) or (result.get("markdown", "") if hasattr(result, "get") else "")
        if not job_urls and markdown:
            job_urls = re.findall(
                r'https://dailyremote\.com/remote-job/[^\s\)\"\]]+', markdown
            )

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for u in job_urls:
            if u not in seen:
                seen.add(u)
                unique_urls.append(u)

        print(f"  Found {len(unique_urls)} job URLs on page {page}")
        return unique_urls

    except Exception as e:
        print(f"  [ERROR] Failed to scrape listing page {page}: {e}")
        return []


def scrape_job_detail(app, url: str) -> dict:
    """Scrape one job detail page. Returns {url, markdown, error}."""
    try:
        result = app.scrape(url, formats=["markdown"])
        markdown = getattr(result, "markdown", None) or (result.get("markdown", "") if hasattr(result, "get") else "")
        if not markdown:
            return {"url": url, "markdown": "", "error": "Empty markdown returned"}
        return {"url": url, "markdown": markdown, "error": None}
    except Exception as e:
        return {"url": url, "markdown": "", "error": str(e)}


def main():
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY not found in environment")

    app = firecrawl.FirecrawlApp(api_key=api_key)

    # Step 1: Collect all job detail URLs from listing pages
    print(f"\n=== Scraping {MAX_PAGES} listing page(s) ===")
    all_job_urls = []
    for page in range(1, MAX_PAGES + 1):
        urls = scrape_listing_page(app, page)
        all_job_urls.extend(urls)
        time.sleep(DELAY_SECONDS)

    # Deduplicate across pages
    seen = set()
    unique_job_urls = []
    for u in all_job_urls:
        if u not in seen:
            seen.add(u)
            unique_job_urls.append(u)

    print(f"\nTotal unique job URLs found: {len(unique_job_urls)}")

    if not unique_job_urls:
        print("[ERROR] No job URLs found. Check URL patterns or Firecrawl response.")
        return

    # Step 2: Scrape each job detail page
    print(f"\n=== Scraping {len(unique_job_urls)} job detail page(s) ===")
    results = []
    succeeded = 0
    failed = 0

    for i, url in enumerate(unique_job_urls, 1):
        print(f"  [{i}/{len(unique_job_urls)}] {url}")
        record = scrape_job_detail(app, url)
        results.append(record)
        if record["error"]:
            print(f"    [ERROR] {record['error']}")
            failed += 1
        else:
            succeeded += 1
        time.sleep(DELAY_SECONDS)

    # Step 3: Save to .tmp/raw_jobs.json
    os.makedirs(".tmp", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n=== Summary ===")
    print(f"  Total attempted: {len(unique_job_urls)}")
    print(f"  Succeeded:       {succeeded}")
    print(f"  Failed:          {failed}")
    print(f"  Output:          {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
