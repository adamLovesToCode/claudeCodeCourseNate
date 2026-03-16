"""
scrape_competitor.py

Scrapes a single competitor URL using Firecrawl, then uses Claude to extract
structured data about their t-shirt product, fit approach, pricing, and features.

Usage:
    python tools/scrape_competitor.py <url>

Outputs: .tmp/scraped/competitor_{slug}.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

import anthropic
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()

PRICING_HINTS = ["pricing", "price", "plans", "shop", "order", "buy", "cost", "order-now", "preise", "bestellen", "kaufen"]
OUTPUT_DIR = ".tmp/scraped"

EXTRACTION_PROMPT = """You are a data extraction assistant. Extract structured information from the following competitor website content.

Focus especially on: how they handle custom sizing and fit for t-shirts, whether customers input body measurements, how the t-shirt is produced, and their pricing.

Return a JSON object with exactly these fields (use null if information is not available):
{{
  "company_name": "string or null",
  "tagline": "string or null",
  "target_audience": "who is this for?",
  "product_type": "what exactly do they sell? Be specific about t-shirts vs other garments.",
  "customization_level": "none | limited | moderate | high | full_bespoke",
  "measurement_method": "self_input | body_scan | ai_sizing | standard_sizes | stylist | unknown",
  "cutting_pattern_generated": "yes | no | unknown",
  "key_features": ["list", "of", "features"],
  "pricing_model": "subscription | per_item | tiered | custom_quote | not_found",
  "price_points": ["list of specific prices or ranges, e.g. '49 EUR per t-shirt'"],
  "production_model": "on_demand | inventory | hybrid | unknown",
  "technologies_mentioned": ["e.g. 3D fitting, body scan, AI sizing"],
  "fit_claims": ["specific claims they make about fit accuracy"],
  "market_focus": ["list countries or regions they target, e.g. Germany, Europe, USA"]
}}

Return ONLY the JSON object. No markdown fences, no commentary.

HOMEPAGE CONTENT:
{homepage}

PRICING PAGE CONTENT:
{pricing}"""


def url_to_slug(url: str) -> str:
    domain = urlparse(url).netloc.lower().replace("www.", "").replace(".", "-")
    return re.sub(r"[^a-z0-9-]", "", domain)


def find_pricing_url(links: list, base_domain: str) -> str | None:
    for link in links:
        if not isinstance(link, str):
            continue
        parsed = urlparse(link)
        if base_domain not in parsed.netloc:
            continue
        path = parsed.path.lower()
        if any(hint in path for hint in PRICING_HINTS):
            return link
    return None


def scrape_competitor(url: str, output_dir: str = OUTPUT_DIR) -> dict:
    fc = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    claude = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    domain = urlparse(url).netloc.lower().replace("www.", "")
    slug = url_to_slug(url)
    output_path = os.path.join(output_dir, f"competitor_{slug}.json")

    os.makedirs(output_dir, exist_ok=True)

    # --- Scrape homepage ---
    print(f"Scraping homepage: {url}")
    try:
        home_result = fc.scrape(
            url,
            formats=["markdown", "links"],
            only_main_content=True,
            timeout=30000,
        )
        homepage_md = home_result.markdown or ""
        raw_links = home_result.links or []
    except Exception as e:
        print(f"  Blocked or failed: {e}")
        record = {
            "url": url,
            "domain": domain,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scrape_status": "blocked",
            "error": str(e),
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        return record

    if not homepage_md or len(homepage_md) < 100:
        print("  Got empty/thin response — marking as blocked")
        record = {
            "url": url,
            "domain": domain,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "scrape_status": "blocked",
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)
        return record

    # --- Try to find and scrape a pricing page ---
    pricing_md = None
    pricing_url = find_pricing_url(raw_links, domain)
    if pricing_url:
        print(f"  Scraping pricing page: {pricing_url}")
        try:
            pricing_result = fc.scrape(
                pricing_url,
                formats=["markdown"],
                only_main_content=True,
                timeout=20000,
            )
            pricing_md = pricing_result.markdown or None
        except Exception as e:
            print(f"  Pricing page failed: {e}")

    # --- Extract structured data via Claude ---
    print("  Extracting structured data via Claude...")
    prompt = EXTRACTION_PROMPT.format(
        homepage=homepage_md[:6000],
        pricing=pricing_md[:3000] if pricing_md else "Not available",
    )
    try:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text.strip()
        raw_text = re.sub(r"^```json\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)
        extracted = json.loads(raw_text)
        confidence = "high"
    except Exception as e:
        print(f"  Extraction failed: {e}")
        extracted = {}
        confidence = "failed"

    record = {
        "url": url,
        "domain": domain,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "scrape_status": "ok",
        "extraction_confidence": confidence,
        "pricing_page_found": pricing_url is not None,
        "raw_homepage_length": len(homepage_md),
        **extracted,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    print(f"  Saved to {output_path}")
    return record


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/scrape_competitor.py <url>")
        sys.exit(1)
    result = scrape_competitor(sys.argv[1])
    print(json.dumps(result, indent=2))
