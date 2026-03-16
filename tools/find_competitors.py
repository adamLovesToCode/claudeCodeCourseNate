"""
find_competitors.py

Uses Firecrawl search to discover 5-8 competitor URLs in the made-to-measure
t-shirt / custom fit apparel niche, focused on the German and European market.

Outputs: .tmp/competitors_raw.json
"""

import json
import os
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

SEARCH_QUERIES = [
    "made to measure t-shirt online Europe custom fit body measurements",
    "maßgeschneidertes T-Shirt online bestellen Deutschland Körpermaße",
    "bespoke custom t-shirt ecommerce Germany Austria Switzerland",
    "Maßshirt online individuell Körpermaße eingeben",
    "custom fit t-shirt slim athletic men Europe online shop",
    "maßgeschneiderte T-Shirts online Körpermaße Schneider",
    "made to measure t-shirt European brand slim fit custom sizing",
]

OUTPUT_PATH = ".tmp/competitors_raw.json"


def find_competitors(
    business_info: dict,
    num_competitors: int = 8,
    output_path: str = OUTPUT_PATH,
) -> list:
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    seen_domains = set()
    results = []

    for query in SEARCH_QUERIES:
        if len(results) >= num_competitors:
            break

        print(f"Searching: {query}")
        try:
            search_result = app.search(query, limit=5)
            # v4: search() returns SearchData directly with .web list
            web_entries = []
            if hasattr(search_result, "web") and search_result.web:
                web_entries = search_result.web
            elif isinstance(search_result, list):
                web_entries = search_result
        except Exception as e:
            print(f"  Search failed: {e}")
            continue

        for entry in web_entries:
            url = entry.url if hasattr(entry, "url") else entry.get("url", "")
            if not url:
                continue

            domain = urlparse(url).netloc.lower().replace("www.", "")
            if domain in seen_domains:
                continue

            seen_domains.add(domain)
            results.append(
                {
                    "url": url,
                    "title": entry.title if hasattr(entry, "title") else entry.get("title", ""),
                    "snippet": entry.description if hasattr(entry, "description") else entry.get("description", ""),
                    "query_source": query,
                    "domain": domain,
                }
            )
            print(f"  Found: {domain}")

            if len(results) >= num_competitors:
                break

    if len(results) < 3:
        raise ValueError(
            f"Only found {len(results)} competitors. Try broadening keywords or check your FIRECRAWL_API_KEY."
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} competitors to {output_path}")
    return results


if __name__ == "__main__":
    business_info_path = "business_info/business_info.json"
    with open(business_info_path, encoding="utf-8") as f:
        business_info = json.load(f)

    competitors = find_competitors(business_info)
    print(json.dumps(competitors, indent=2))
