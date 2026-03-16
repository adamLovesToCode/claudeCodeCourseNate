# Competitor Research Analysis Workflow

## Objective
Generate a comprehensive competitor analysis PDF for a made-to-measure t-shirt business.
The report covers 5–8 competitors with profiles, feature comparison matrix, pricing landscape,
gaps in the market, and strategic recommendations — all focused on the custom-tailoring and
fit-technology angle.

## Required Inputs
- `business_info/business_info.json` — must exist and be populated before running
- `.env` with `FIRECRAWL_API_KEY` and `ANTHROPIC_API_KEY`
- Python dependencies installed: `pip install -r requirements.txt`

## Outputs
| File | Description |
|------|-------------|
| `.tmp/competitors_raw.json` | Discovered competitor URLs from Firecrawl search |
| `.tmp/scraped/competitor_*.json` | One file per scraped competitor |
| `.tmp/analysis.json` | Structured analysis from Claude |
| `.tmp/analysis_raw.txt` | Raw Claude output (debug, overwritten each run) |
| `.tmp/competitor_analysis_{timestamp}.pdf` | **Final deliverable** |

---

## Step-by-Step Execution

### Step 1 — Verify Inputs
1. Confirm `business_info/business_info.json` exists. If not, tell the user and stop.
2. Confirm `.env` contains `FIRECRAWL_API_KEY` and `ANTHROPIC_API_KEY`. If not, tell the user and stop.
3. Confirm Python dependencies are installed (`firecrawl-py`, `anthropic`, `fpdf2`, `python-dotenv`).
4. Create `.tmp/scraped/` directory if it doesn't exist.

### Step 2 — Find Competitors
Run:
```
python tools/find_competitors.py
```
- Expected output: `.tmp/competitors_raw.json` with 5–8 competitor entries
- If fewer than 3 URLs found: the script raises a ValueError. Widen keyword search or ask
  the user to provide competitor URLs manually.

### Step 3 — Scrape Each Competitor
For each URL in `.tmp/competitors_raw.json`, run:
```
python tools/scrape_competitor.py <url>
```
- Run sequentially (not in parallel) to respect rate limits — wait ~1 second between calls
- Each run saves a file to `.tmp/scraped/competitor_{slug}.json`
- Blocked sites are saved with `"scrape_status": "blocked"` — do not retry, continue to next
- Track counts: `scraped_ok` vs `scraped_blocked`
- If fewer than 3 successful scrapes after all URLs: surface blocked domains to user and ask
  if they want to provide alternative URLs

### Step 4 — Analyze
Run:
```
python tools/analyze_competitors.py
```
- Loads all non-blocked scraped files and calls Claude for analysis
- Expected output: `.tmp/analysis.json`
- If the script raises a ValueError (invalid JSON or too few competitors): check
  `.tmp/analysis_raw.txt` for the raw Claude output, then attempt one re-run

### Step 5 — Generate PDF
Run:
```
python tools/generate_pdf.py
```
- Expected output: `.tmp/competitor_analysis_{timestamp}.pdf`
- The script prints the exact filename to stdout — capture it
- Verify the file exists before reporting to the user

### Step 6 — Report to User
Tell the user:
- The exact PDF path (e.g., `.tmp/competitor_analysis_20260316_143022.pdf`)
- How many competitors were profiled and how many were skipped/blocked
- The top 2 strategic recommendations (from `analysis.json["strategic_recommendations"]`)
- Any data quality issues (from `analysis.json["data_quality_notes"]`)

---

## Edge Case Handling

| Situation | Response |
|-----------|----------|
| Competitor site blocks Firecrawl | Skip, note in `data_quality_notes` in PDF appendix |
| No pricing page found | Use homepage data only; Claude marks pricing as "Not disclosed" |
| Fewer than 3 usable scrapes | Stop after Step 3, ask user for additional URLs |
| Claude returns invalid JSON in analysis | Save raw to `.tmp/analysis_raw.txt`, re-run once |
| PDF generation fails | Verify fpdf2 is installed; check `.tmp/analysis.json` is valid |
| Search finds irrelevant results | Filter by snippet relevance before saving; re-run with tighter queries |
| Firecrawl rate limit hit | Wait 60 seconds, then retry the failed call once |

---

## Rate Limit Notes
- **Firecrawl**: ~1 credit per search query, ~1 credit per scrape. Free tier ~500 credits/month.
  Space scrape calls at least 1 second apart.
- **Anthropic**: Extraction call per competitor (~1,000 tokens) + one analysis call (~13,000 tokens).
  Total per run: ~20,000–25,000 tokens (~$0.06 at Sonnet pricing).

---

## Workflow Improvement Log
*(Update this section when you discover new constraints, better approaches, or useful findings)*

- **2026-03-16** — Initial workflow created. Firecrawl search + scrape → Claude extraction → Claude analysis → fpdf2 PDF.
