"""
Tool: extract_and_export_jobs.py
Purpose: Read raw scraped markdown from .tmp/raw_jobs.json, use Claude Haiku to extract
         structured job fields, and export the results to .tmp/jobs.xlsx.
"""

import json
import os

import anthropic
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

INPUT_PATH = ".tmp/raw_jobs.json"
OUTPUT_PATH = ".tmp/jobs.xlsx"
MODEL = "claude-haiku-4-5-20251001"

COLUMN_ORDER = [
    "job_url",
    "title",
    "company",
    "location",
    "job_type",
    "experience_level",
    "salary",
    "date_posted",
    "tags_skills",
    "full_description",
    "scrape_error",
]

EXTRACTION_SYSTEM_PROMPT = """You are a structured data extraction assistant. You will be given the markdown content of a job listing page.

Extract the following fields and return ONLY a valid JSON object with exactly these keys.
Use null for any field you cannot find. Do not include any explanation or text outside the JSON object.

{
  "title": "string or null",
  "company": "string or null",
  "location": "string or null",
  "job_type": "string or null",
  "experience_level": "string or null",
  "salary": "string or null",
  "date_posted": "string or null",
  "tags_skills": "comma-separated string of skills/tags or null",
  "full_description": "the complete job description text or null"
}"""


def extract_job_fields(client: anthropic.Anthropic, markdown: str) -> dict:
    """Call Claude Haiku and return parsed dict of job fields."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Extract job fields from this content:\n\n{markdown[:8000]}",
            }
        ],
    )
    raw_text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```", 2)[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()
    return json.loads(raw_text)


def build_row(record: dict, extracted: dict | None, parse_error: str | None = None) -> dict:
    """Merge extracted fields with job_url and error info into a flat dict."""
    row = {"job_url": record["url"], "scrape_error": record.get("error")}
    fields = ["title", "company", "location", "job_type", "experience_level",
              "salary", "date_posted", "tags_skills", "full_description"]

    if extracted:
        for field in fields:
            row[field] = extracted.get(field)
    else:
        for field in fields:
            row[field] = None
        if parse_error:
            row["full_description"] = f"[Extraction failed] {parse_error}"

    return row


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    client = anthropic.Anthropic(api_key=api_key)

    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(f"Input file not found: {INPUT_PATH}. Run scrape_job_listings.py first.")

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)

    print(f"\n=== Extracting fields from {len(records)} job record(s) ===")
    rows = []
    succeeded = 0
    failed_scrape = 0
    failed_extract = 0

    for i, record in enumerate(records, 1):
        url = record.get("url", "unknown")
        print(f"  [{i}/{len(records)}] {url}")

        # Skip if scrape failed
        if record.get("error") or not record.get("markdown"):
            print(f"    [SKIP] Scrape error: {record.get('error')}")
            rows.append(build_row(record, None))
            failed_scrape += 1
            continue

        # Extract with Claude
        try:
            extracted = extract_job_fields(client, record["markdown"])
            rows.append(build_row(record, extracted))
            succeeded += 1
        except json.JSONDecodeError as e:
            print(f"    [WARN] JSON parse error: {e}")
            rows.append(build_row(record, None, parse_error=str(e)))
            failed_extract += 1
        except Exception as e:
            print(f"    [ERROR] Extraction failed: {e}")
            rows.append(build_row(record, None, parse_error=str(e)))
            failed_extract += 1

    # Build DataFrame and export
    df = pd.DataFrame(rows)
    for col in COLUMN_ORDER:
        if col not in df.columns:
            df[col] = None
    df = df[COLUMN_ORDER]

    os.makedirs(".tmp", exist_ok=True)
    df.to_excel(OUTPUT_PATH, index=False, engine="openpyxl")

    print(f"\n=== Summary ===")
    print(f"  Total records:     {len(records)}")
    print(f"  Extracted OK:      {succeeded}")
    print(f"  Scrape failures:   {failed_scrape}")
    print(f"  Extract failures:  {failed_extract}")
    print(f"  Output:            {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
