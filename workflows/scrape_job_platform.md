# Workflow: Scrape Job Platform → Excel

## Objective
Scrape React developer job listings from dailyremote.com, capture full job descriptions by following each listing's URL, and export structured data to Excel for review.

## Inputs
- Search URL: `https://dailyremote.com/?search=react%20developer&page={N}`
- Pages to scrape: 2 (configurable via MAX_PAGES in tool)
- Output path: `.tmp/jobs.xlsx`
- Intermediate: `.tmp/raw_jobs.json`

## Tool Execution Order

### Step 1: Scrape raw content
```
python tools/scrape_job_listings.py
```
- Scrapes listing pages 1–2 to collect job detail URLs
- Follows each URL and scrapes the full job detail page
- Saves raw markdown to `.tmp/raw_jobs.json`
- Prints summary: total attempted / succeeded / failed

**Check before proceeding:** Confirm `.tmp/raw_jobs.json` exists and has >0 successful records. If 0 succeeded, do not run Step 2 — diagnose the Firecrawl issue first (check API key, rate limits, URL patterns).

### Step 2: Extract fields and export
```
python tools/extract_and_export_jobs.py
```
- Reads `.tmp/raw_jobs.json`
- Calls Claude Haiku to extract structured fields from each job's markdown
- Builds a DataFrame and writes `.tmp/jobs.xlsx`
- Prints row count on completion

## Expected Outputs
- `.tmp/raw_jobs.json` — intermediate raw scrape data (checkpoint; safe to reuse if re-running extraction)
- `.tmp/jobs.xlsx` — final Excel file with columns: `job_url`, `title`, `company`, `location`, `job_type`, `experience_level`, `salary`, `date_posted`, `tags_skills`, `full_description`, `scrape_error`

## Known Constraints
- **Rate limiting:** 1 second delay between Firecrawl requests (free tier limit)
- **Premium listings:** Company name may be hidden; Claude will extract as "Hidden" or similar
- **Salary:** Frequently not disclosed; expect many null values in that column
- **Job URL extraction:** Filter listing page links by `/remote-job/` pattern; other links are navigation/ads
- **Firecrawl `links` format:** Request `formats=["markdown", "links"]` on listing pages; `formats=["markdown"]` on detail pages only

## Edge Cases
- If a job detail page fails to scrape → store row with nulls and error message in `scrape_error` column; continue to next job
- If Claude returns malformed JSON → store raw response text in `full_description`, null all other fields; do not skip the row
- If `.tmp/` directory does not exist → create it before writing output
- If a listing page returns 0 job URLs → log a warning and continue to next page

## Self-Improvement Notes
- Update this workflow if new URL patterns are discovered on dailyremote.com
- If Firecrawl's `links` format changes behavior, fall back to regex parsing of markdown: `re.findall(r'https://dailyremote\.com/remote-job/[^\s\)\"]+', markdown)`
- If Claude extraction accuracy drops, consider adding few-shot examples to the system prompt
- **Claude Haiku wraps JSON in markdown code fences** (```json```) even when instructed not to -- `extract_and_export_jobs.py` strips these before parsing. Safe to leave the strip logic in place for other models too (no-op on clean JSON)
- **Firecrawl SDK v4.x**: use `app.scrape(url, formats=[...])` -- `scrape_url()` was removed in v4.x
