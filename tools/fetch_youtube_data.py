"""
fetch_youtube_data.py
Step 1 of the YouTube Content Insights workflow.
Searches YouTube by keyword, fetches video + channel stats, saves to .tmp/youtube_raw.json.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv()

# ── Configuration ──────────────────────────────────────────────────────────────
KEYWORDS = [
    "tailored t-shirts",
    "custom fit t-shirt",
    "bespoke clothing",
    "fitted t-shirt review",
    "menswear style tips",
    "clothing alterations",
    "luxury basics clothing",
]

MAX_RESULTS_PER_KEYWORD = 10
DAYS_BACK = 90  # Search videos published within this many days
OUTPUT_PATH = Path(".tmp/youtube_raw.json")


# ── Helpers ────────────────────────────────────────────────────────────────────
def get_published_after(days_back: int) -> str:
    """Return RFC 3339 timestamp for N days ago."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")


def search_videos(youtube, keyword: str, published_after: str) -> list[str]:
    """Search YouTube for a keyword. Returns list of video IDs."""
    try:
        response = youtube.search().list(
            q=keyword,
            part="id,snippet",
            type="video",
            maxResults=MAX_RESULTS_PER_KEYWORD,
            order="viewCount",
            publishedAfter=published_after,
        ).execute()
        ids = [item["id"]["videoId"] for item in response.get("items", [])]
        print(f"  '{keyword}': {len(ids)} videos found")
        return ids
    except HttpError as e:
        print(f"  ERROR searching '{keyword}': {e}")
        return []


def get_video_details(youtube, video_ids: list[str], keyword_map: dict) -> list[dict]:
    """Fetch full stats + snippet for a list of video IDs (batched by 50)."""
    videos = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        try:
            response = youtube.videos().list(
                part="statistics,snippet,contentDetails",
                id=",".join(batch),
            ).execute()
            for item in response.get("items", []):
                stats = item.get("statistics", {})
                snippet = item.get("snippet", {})
                videos.append(
                    {
                        "video_id": item["id"],
                        "title": snippet.get("title", ""),
                        "channel_title": snippet.get("channelTitle", ""),
                        "channel_id": snippet.get("channelId", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "description": snippet.get("description", "")[:500],
                        "tags": snippet.get("tags", []),
                        "category_id": snippet.get("categoryId", ""),
                        "view_count": int(stats.get("viewCount", 0) or 0),
                        "like_count": int(stats.get("likeCount", 0) or 0),
                        "comment_count": int(stats.get("commentCount", 0) or 0),
                        "duration": item.get("contentDetails", {}).get("duration", ""),
                        "keywords_matched": keyword_map.get(item["id"], []),
                    }
                )
        except HttpError as e:
            print(f"  ERROR fetching video details (batch {i}): {e}")
    return videos


def get_channel_details(youtube, channel_ids: list[str]) -> list[dict]:
    """Fetch stats + snippet for a list of channel IDs (batched by 50)."""
    channels = []
    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i : i + 50]
        try:
            response = youtube.channels().list(
                part="statistics,snippet",
                id=",".join(batch),
            ).execute()
            for item in response.get("items", []):
                stats = item.get("statistics", {})
                snippet = item.get("snippet", {})
                channels.append(
                    {
                        "channel_id": item["id"],
                        "channel_title": snippet.get("title", ""),
                        "description": snippet.get("description", "")[:300],
                        "subscriber_count": int(stats.get("subscriberCount", 0) or 0),
                        "video_count": int(stats.get("videoCount", 0) or 0),
                        "view_count": int(stats.get("viewCount", 0) or 0),
                        "country": snippet.get("country", ""),
                    }
                )
        except HttpError as e:
            print(f"  ERROR fetching channel details (batch {i}): {e}")
    return channels


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env")

    youtube = build("youtube", "v3", developerKey=api_key)
    published_after = get_published_after(DAYS_BACK)

    print(f"Searching videos published after {published_after}")
    print(f"Keywords: {len(KEYWORDS)}\n")

    # Collect video IDs per keyword, track which keywords matched each video
    keyword_map: dict[str, list[str]] = {}  # video_id -> [keywords]
    all_video_ids: list[str] = []

    for keyword in KEYWORDS:
        ids = search_videos(youtube, keyword, published_after)
        for vid_id in ids:
            if vid_id not in keyword_map:
                keyword_map[vid_id] = []
                all_video_ids.append(vid_id)
            keyword_map[vid_id].append(keyword)

    print(f"\nUnique videos: {len(all_video_ids)}")

    # Fetch full video details
    print("Fetching video details...")
    videos = get_video_details(youtube, all_video_ids, keyword_map)

    # Fetch channel details for unique channels
    channel_ids = list({v["channel_id"] for v in videos if v["channel_id"]})
    print(f"Fetching details for {len(channel_ids)} channels...")
    channels = get_channel_details(youtube, channel_ids)

    # Save output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "days_back": DAYS_BACK,
        "keywords": KEYWORDS,
        "videos": videos,
        "channels": channels,
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nDone. Saved {len(videos)} videos and {len(channels)} channels to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
