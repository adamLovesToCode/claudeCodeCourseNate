"""
send_email_report.py
Step 4 of the YouTube Content Insights workflow.
Authenticates with Gmail via OAuth, sends the .pptx report as an email attachment.
"""

import base64
import glob
import json
import os
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
OAUTH_DIR = Path("oauth")
TOKEN_PATH = OAUTH_DIR / "token.json"
REPORT_PATH = Path(".tmp/youtube_insights_report.pdf")
INSIGHTS_PATH = Path(".tmp/youtube_insights.json")
RECIPIENT = "adam.konopka.dev@gmail.com"
REDIRECT_URI = "http://localhost:8080"


# ── Auth ───────────────────────────────────────────────────────────────────────
def get_credentials_file() -> Path:
    """Glob for the client_secret JSON in the oauth/ directory."""
    matches = glob.glob(str(OAUTH_DIR / "client_secret_*.json"))
    if not matches:
        raise FileNotFoundError(
            "No client_secret_*.json found in oauth/. "
            "Download OAuth credentials from Google Cloud Console."
        )
    return Path(matches[0])


def get_gmail_service():
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("No valid token found. Starting browser authorization flow...")
            creds_file = get_credentials_file()
            flow = Flow.from_client_secrets_file(
                str(creds_file),
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI,
            )
            auth_url, _ = flow.authorization_url(prompt="consent")
            print(f"\nOpen this URL in your browser:\n\n  {auth_url}\n")
            print(
                "After authorizing, your browser will redirect to http://localhost:8080/?code=...\n"
                "Copy the FULL redirect URL and paste it here:"
            )
            redirect_response = input("Redirect URL: ").strip()
            flow.fetch_token(authorization_response=redirect_response)
            creds = flow.credentials

        OAUTH_DIR.mkdir(exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())
        print(f"Token saved to {TOKEN_PATH}")

    return build("gmail", "v1", credentials=creds)


# ── Email builder ──────────────────────────────────────────────────────────────
def build_email_html(insights: dict) -> str:
    s = insights["summary"]
    top_kw = s.get("top_keyword_by_views", "N/A")
    top_video = insights["top_videos_by_views"][0] if insights["top_videos_by_views"] else {}

    return f"""
<html><body style="font-family: Arial, sans-serif; color: #1a1a1a; max-width: 620px; margin: 0 auto;">

<div style="background: #0D1B2A; padding: 30px 40px; border-radius: 8px 8px 0 0;">
  <h1 style="color: #F5C518; margin: 0; font-size: 24px;">YouTube Content Insights Report</h1>
  <p style="color: #A0B0C0; margin: 8px 0 0;">Tailored Clothing &amp; Custom T-Shirts Niche &nbsp;·&nbsp; {datetime.now().strftime('%B %d, %Y')}</p>
</div>

<div style="background: #f9f9f9; padding: 30px 40px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 8px 8px;">

  <p style="font-size: 15px;">Hi Adam,</p>
  <p style="font-size: 15px;">Your weekly YouTube niche intelligence report is attached. Here's a quick snapshot:</p>

  <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
    <tr style="background: #0D1B2A; color: white;">
      <th style="padding: 10px 14px; text-align: left; font-size: 13px;">Metric</th>
      <th style="padding: 10px 14px; text-align: left; font-size: 13px;">Value</th>
    </tr>
    <tr style="background: #fff;">
      <td style="padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #eee;">Videos Analyzed</td>
      <td style="padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #eee;"><strong>{s['total_videos_analyzed']}</strong></td>
    </tr>
    <tr style="background: #f5f5f5;">
      <td style="padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #eee;">Channels Tracked</td>
      <td style="padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #eee;"><strong>{s['total_channels']}</strong></td>
    </tr>
    <tr style="background: #fff;">
      <td style="padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #eee;">Avg Engagement Rate</td>
      <td style="padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #eee;"><strong>{s['avg_engagement_rate']}%</strong></td>
    </tr>
    <tr style="background: #f5f5f5;">
      <td style="padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #eee;">Top Keyword</td>
      <td style="padding: 9px 14px; font-size: 13px; border-bottom: 1px solid #eee;"><strong>{top_kw}</strong></td>
    </tr>
    <tr style="background: #fff;">
      <td style="padding: 9px 14px; font-size: 13px;">#1 Video</td>
      <td style="padding: 9px 14px; font-size: 13px;"><strong>{top_video.get('title', 'N/A')[:60]}</strong></td>
    </tr>
  </table>

  <p style="font-size: 14px; color: #555;">The full report is attached as an art-directed PDF.</p>

  <p style="font-size: 13px; color: #999; margin-top: 30px; border-top: 1px solid #eee; padding-top: 16px;">
    Generated automatically by your YouTube Content Insights workflow.<br>
    Run <code>python tools/fetch_youtube_data.py</code> followed by the remaining tools to refresh.
  </p>
</div>
</body></html>
"""


def build_message(service_account_email: str, insights: dict) -> dict:
    report_date = datetime.now().strftime("%Y-%m-%d")
    subject = f"YouTube Content Insights — Tailored Clothing Niche ({report_date})"

    msg = MIMEMultipart("mixed")
    msg["To"] = RECIPIENT
    msg["Subject"] = subject

    # HTML body
    html_part = MIMEText(build_email_html(insights), "html")
    msg.attach(html_part)

    # Attach .pdf
    with open(REPORT_PATH, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=f"youtube_insights_{report_date}.pdf",
        )
        msg.attach(attachment)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"{REPORT_PATH} not found. Run generate_pdf_report.py first.")
    if not INSIGHTS_PATH.exists():
        raise FileNotFoundError(f"{INSIGHTS_PATH} not found. Run analyze_insights.py first.")

    insights = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8"))

    print("Authenticating with Gmail...")
    service = get_gmail_service()

    # Get sender address
    profile = service.users().getProfile(userId="me").execute()
    sender_email = profile.get("emailAddress", "me")
    print(f"Sending as: {sender_email} → {RECIPIENT}")

    message = build_message(sender_email, insights)
    result = service.users().messages().send(userId="me", body=message).execute()

    print(f"\n✓ Email sent — Message ID: {result['id']}")
    print(f"  Report delivered to {RECIPIENT}")


if __name__ == "__main__":
    main()
