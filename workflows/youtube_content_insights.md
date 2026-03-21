# Workflow: YouTube Content Insights → PDF Report → Email

## Objective
Discover trending YouTube content in the tailored t-shirt / clothing niche, analyze engagement and performance metrics, generate an art-directed PDF report (canvas-design "Sartorial Signal" philosophy), and email it to adam.konopka.dev@gmail.com.

## Required Inputs
- `GEMINI_API_KEY` in `.env` — used as the YouTube Data API v3 key (same Google Cloud project)
- `oauth/client_secret_*.json` — Gmail OAuth credentials (already in repo)
- `oauth/token.json` — auto-generated on first run; browser auth will open if missing

## Prerequisites (one-time setup)
1. **Enable YouTube Data API v3**: Google Cloud Console → project `gen-lang-client-0936416768` → APIs & Services → Library → search "YouTube Data API v3" → Enable
2. **Authorize Gmail redirect URI**: Google Cloud Console → project → Credentials → click the OAuth 2.0 Client ID → Authorized redirect URIs → add `http://localhost:8080`
3. Install dependencies: `pip install -r requirements.txt`

## Execution Order

### Step 1 — Fetch YouTube Data
```bash
python tools/fetch_youtube_data.py
```
- Searches 7 keywords across YouTube Data API v3
- Fetches video stats + channel stats
- Output: `.tmp/youtube_raw.json`
- Expected: "Found X videos across Y keywords"
- Quota cost: ~5–7 searches × 100 + ~100 video lookups × 1 ≈ 600–800 units (< 10% of 10K free daily quota)

### Step 2 — Analyze Insights
```bash
python tools/analyze_insights.py
```
- Computes engagement rate, views/day, like ratio per video
- Builds top-10 rankings and keyword performance breakdown
- Generates 4 chart PNGs into `.tmp/charts/`
- Output: `.tmp/youtube_insights.json`

### Step 3 — Generate PDF Report
```bash
python tools/generate_pdf_report.py
```
- Reads `.tmp/youtube_insights.json` + chart PNGs
- Produces 4-page art-directed PDF using "Sartorial Signal" design philosophy
- Output: `.tmp/youtube_insights_report.pdf`

### Step 4 — Send Email
```bash
python tools/send_email_report.py
```
- **First run only**: script prints a Google auth URL — open it in your browser, authorize, copy the full redirect URL (`http://localhost:8080/?code=...`) from the address bar, paste it back into the terminal → `oauth/token.json` saved. All future runs are fully automatic.
- Sends `.pdf` as attachment to adam.konopka.dev@gmail.com
- Prints: "Email sent — Message ID: [id]"

## Search Keywords
Defined in `tools/fetch_youtube_data.py` — edit `KEYWORDS` list to change scope:
```python
KEYWORDS = [
    "tailored t-shirts",
    "custom fit t-shirt",
    "bespoke clothing",
    "fitted t-shirt review",
    "menswear style tips",
    "clothing alterations",
    "luxury basics clothing",
]
```

## Expected Outputs
| File | Description |
|------|-------------|
| `.tmp/youtube_raw.json` | Raw API response: videos + channels |
| `.tmp/youtube_insights.json` | Computed metrics and rankings |
| `.tmp/charts/*.png` | 4 chart images used in the PDF |
| `.tmp/youtube_insights_report.pdf` | Art-directed PDF report (4 pages) |

## PDF Report Structure
| # | Page | Content |
|---|------|---------|
| 1 | Cover | Title, date, key stats strip |
| 2 | Signal Analysis | Keyword bars, engagement table, tag cloud |
| 3 | Top Videos | Table: top 10 by views |
| 4 | Channels & Strategy | Channel table + 6 actionable recommendations |

## Error Handling
| Error | Cause | Fix |
|-------|-------|-----|
| `accessNotConfigured` (403) | YouTube Data API v3 not enabled | Enable it in Google Cloud Console (see Prerequisites) |
| `quotaExceeded` (403) | Exceeded 10K daily units | Wait until midnight PT for reset |
| `redirect_uri_mismatch` | localhost:8080 not in OAuth allowlist | Add `http://localhost:8080` to authorized redirect URIs |
| Zero results for keyword | No matching videos in date window | Check keyword spelling; widen `publishedAfter` in fetch script |
| Token expired | `oauth/token.json` stale | Delete `oauth/token.json` and re-run step 4 |

## Known Constraints
- YouTube search results cap at 50 per query (using `maxResults=10` per keyword = ~70 unique videos after dedup)
- `likeCount` may be hidden by channel owners — treat null as 0
- API quota resets daily at midnight Pacific Time
- Gmail OAuth token lasts ~1 hour; refresh token is long-lived (stored in `oauth/token.json`)
