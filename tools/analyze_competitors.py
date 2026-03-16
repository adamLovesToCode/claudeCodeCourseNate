"""
analyze_competitors.py

Loads business_info.json and all scraped competitor files, sends everything
to Claude for a structured competitive analysis, and saves the result.

Outputs: .tmp/analysis.json
"""

import json
import os
import re
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

BUSINESS_INFO_PATH = "business_info/business_info.json"
SCRAPED_DIR = ".tmp/scraped"
OUTPUT_PATH = ".tmp/analysis.json"
RAW_OUTPUT_PATH = ".tmp/analysis_raw.txt"

SYSTEM_PROMPT = """You are a senior market research analyst specializing in fashion technology, \
custom apparel, and e-commerce. You produce rigorous, actionable competitive analyses for \
early-stage startups.

Your analysis must be evidence-based: cite specific features, prices, and positioning observed \
in the competitor data. Do not speculate beyond what the data shows; flag when data was \
unavailable.

The user's core differentiator is TRUE made-to-measure: customers input body measurements, \
a cutting pattern is generated, and a local tailor produces the garment. Focus your analysis \
on how competitors handle fit and customization — do they actually take measurements, or do \
they just offer standard sizes? This distinction is the key competitive lens.

Return a single valid JSON object. No markdown fences, no commentary outside the JSON."""

ANALYSIS_SCHEMA = """{
  "executive_summary": "3-4 sentence strategic overview of the competitive landscape",

  "competitor_profiles": [
    {
      "company_name": "string",
      "url": "string",
      "overview": "2-3 sentence description",
      "target_audience": "string",
      "key_features": ["list"],
      "measurement_approach": "how they handle sizing — be specific",
      "pricing": {
        "model": "string",
        "range": "string",
        "notes": "string"
      },
      "strengths": ["list of 3-5 strengths"],
      "weaknesses": ["list of 3-5 weaknesses"],
      "relevance_to_user": "direct | adjacent | indirect"
    }
  ],

  "feature_matrix": {
    "dimensions": [
      "Customer inputs body measurements",
      "Cutting pattern generated per customer",
      "Made by a human tailor",
      "On-demand production (no inventory)",
      "Fit guarantee",
      "Price transparency",
      "Fast delivery (<14 days)",
      "Wide product range"
    ],
    "user_business": {
      "Customer inputs body measurements": "yes",
      "Cutting pattern generated per customer": "yes",
      "Made by a human tailor": "yes",
      "On-demand production (no inventory)": "yes",
      "Fit guarantee": "unknown",
      "Price transparency": "yes",
      "Fast delivery (<14 days)": "unknown",
      "Wide product range": "no"
    },
    "competitors": {
      "CompanyName": {
        "Customer inputs body measurements": "yes|no|partial|unknown"
      }
    }
  },

  "pricing_landscape": {
    "market_low": "string — cheapest option found",
    "market_high": "string — most expensive found",
    "typical_range": "string — where most competitors cluster",
    "user_positioning_recommendation": "string — where the user should price",
    "notes": "string"
  },

  "gaps_and_opportunities": [
    {
      "gap": "what is missing or underserved in the market",
      "opportunity": "how the user's business can exploit it",
      "priority": "high | medium | low"
    }
  ],

  "strategic_recommendations": [
    {
      "recommendation": "string — a specific, actionable recommendation",
      "rationale": "why, based on specific competitor evidence",
      "action_items": ["list of concrete next steps"],
      "priority": "high | medium | low"
    }
  ],

  "data_quality_notes": "flag any competitors with missing, blocked, or low-confidence data"
}"""


def load_competitors(scraped_dir: str) -> list:
    competitors = []
    for f in sorted(Path(scraped_dir).glob("competitor_*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("scrape_status") == "blocked":
            print(f"  Skipping blocked: {data.get('domain')}")
            continue
        if data.get("extraction_confidence") == "failed":
            print(f"  Skipping failed extraction: {data.get('domain')}")
            continue
        competitors.append(data)
    return competitors


def analyze_competitors(
    business_info_path: str = BUSINESS_INFO_PATH,
    scraped_dir: str = SCRAPED_DIR,
    output_path: str = OUTPUT_PATH,
) -> dict:
    with open(business_info_path, encoding="utf-8") as f:
        business_info = json.load(f)

    print(f"Loading scraped competitors from {scraped_dir}...")
    competitors = load_competitors(scraped_dir)
    print(f"  Loaded {len(competitors)} usable competitors")

    if len(competitors) < 2:
        raise ValueError(
            f"Only {len(competitors)} usable competitor(s) found. "
            "Re-run scraping or add more competitor URLs."
        )

    user_prompt = f"""Perform a comprehensive competitor analysis for the following business:

BUSINESS OVERVIEW:
{json.dumps(business_info, indent=2)}

COMPETITOR DATA ({len(competitors)} competitors):
{json.dumps(competitors, indent=2)}

Return a JSON object matching this exact schema:
{ANALYSIS_SCHEMA}

Fill in the feature_matrix.competitors section with one entry per competitor from the data above.
Focus on how well each competitor truly delivers made-to-measure fit vs. just offering size customization."""

    print("Calling Claude for analysis...")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text.strip()

    # Save raw output for debugging
    os.makedirs(os.path.dirname(RAW_OUTPUT_PATH), exist_ok=True)
    with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(raw_text)

    # Parse JSON — strip fences if present
    clean = re.sub(r"^```json\s*", "", raw_text)
    clean = re.sub(r"\s*```$", "", clean)

    try:
        analysis = json.loads(clean)
    except json.JSONDecodeError:
        # Try to extract the first {...} block
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            analysis = json.loads(match.group())
        else:
            raise ValueError(
                f"Claude returned invalid JSON. Raw output saved to {RAW_OUTPUT_PATH}"
            )

    if "competitor_profiles" not in analysis:
        raise ValueError(
            f"Analysis JSON missing expected keys. Raw output saved to {RAW_OUTPUT_PATH}"
        )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    print(f"Analysis saved to {output_path}")
    return analysis


if __name__ == "__main__":
    analysis = analyze_competitors()
    print(f"\nExecutive Summary:\n{analysis.get('executive_summary', '')}")
    print(f"\nCompetitors analyzed: {len(analysis.get('competitor_profiles', []))}")
    print(f"Gaps identified: {len(analysis.get('gaps_and_opportunities', []))}")
    print(f"Recommendations: {len(analysis.get('strategic_recommendations', []))}")
