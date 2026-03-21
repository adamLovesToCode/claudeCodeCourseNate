"""
analyze_insights.py
Step 2 of the YouTube Content Insights workflow.
Reads .tmp/youtube_raw.json, computes engagement metrics, generates charts,
saves structured insights to .tmp/youtube_insights.json.
"""

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — must be before pyplot import
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

INPUT_PATH = Path(".tmp/youtube_raw.json")
OUTPUT_PATH = Path(".tmp/youtube_insights.json")
CHARTS_DIR = Path(".tmp/charts")

# Style
sns.set_theme(style="darkgrid")
PALETTE = "#F5C518"
BG_COLOR = "#0D1B2A"
TEXT_COLOR = "#FFFFFF"


# ── Metrics ────────────────────────────────────────────────────────────────────
def compute_video_metrics(df: pd.DataFrame) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    df = df.copy()
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
    df["days_since"] = (now - df["published_at"]).dt.total_seconds() / 86400
    df["days_since"] = df["days_since"].clip(lower=1)

    df["views_per_day"] = df["view_count"] / df["days_since"]
    df["engagement_rate"] = (
        (df["like_count"] + df["comment_count"]) / df["view_count"].replace(0, np.nan) * 100
    ).fillna(0)
    df["like_ratio"] = (
        df["like_count"] / df["view_count"].replace(0, np.nan) * 100
    ).fillna(0)
    return df


# ── Charts ─────────────────────────────────────────────────────────────────────
def _fig_style(fig, ax, title: str):
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.title.set_color(TEXT_COLOR)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.tick_params(colors=TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2A3F5F")
    ax.set_title(title, fontsize=14, fontweight="bold", color=TEXT_COLOR, pad=12)


def chart_top_videos_bar(df: pd.DataFrame) -> Path:
    top = df.nlargest(10, "view_count")[["title", "view_count"]].copy()
    top["title_short"] = top["title"].str[:40] + "…"

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(top["title_short"][::-1], top["view_count"][::-1], color=PALETTE)
    ax.bar_label(bars, fmt="{:,.0f}", color=TEXT_COLOR, padding=4, fontsize=9)
    ax.set_xlabel("View Count", color=TEXT_COLOR)
    _fig_style(fig, ax, "Top 10 Videos by View Count")
    plt.tight_layout()
    path = CHARTS_DIR / "top_videos_bar.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    return path


def chart_engagement_scatter(df: pd.DataFrame) -> Path:
    scatter_df = df[(df["view_count"] > 0) & (df["engagement_rate"] < 20)].copy()
    size = (scatter_df["like_count"] / scatter_df["like_count"].max() * 300 + 20).fillna(20)

    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(
        scatter_df["view_count"],
        scatter_df["engagement_rate"],
        s=size,
        c=PALETTE,
        alpha=0.7,
        edgecolors="#2A3F5F",
    )
    ax.set_xlabel("View Count", color=TEXT_COLOR)
    ax.set_ylabel("Engagement Rate (%)", color=TEXT_COLOR)
    _fig_style(fig, ax, "Views vs Engagement Rate (bubble = likes)")
    plt.tight_layout()
    path = CHARTS_DIR / "engagement_scatter.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    return path


def chart_keyword_heatmap(df: pd.DataFrame, keywords: list[str]) -> Path:
    rows = []
    for kw in keywords:
        kw_df = df[df["keywords_matched"].apply(lambda x: kw in x)]
        rows.append(
            {
                "keyword": kw,
                "avg_views": kw_df["view_count"].mean() if len(kw_df) else 0,
                "avg_engagement": kw_df["engagement_rate"].mean() if len(kw_df) else 0,
                "video_count": len(kw_df),
            }
        )
    kdf = pd.DataFrame(rows).set_index("keyword")
    heat_data = kdf[["avg_views", "avg_engagement", "video_count"]].T

    fig, ax = plt.subplots(figsize=(12, 4))
    sns.heatmap(
        heat_data,
        ax=ax,
        cmap="YlOrBr",
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="#2A3F5F",
        cbar_kws={"label": "Value"},
    )
    ax.set_yticklabels(["Avg Views", "Avg Engagement %", "Video Count"], rotation=0, color=TEXT_COLOR)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", color=TEXT_COLOR)
    _fig_style(fig, ax, "Keyword Performance Heatmap")
    ax.collections[0].colorbar.ax.yaxis.label.set_color(TEXT_COLOR)
    ax.collections[0].colorbar.ax.tick_params(colors=TEXT_COLOR)
    plt.tight_layout()
    path = CHARTS_DIR / "keyword_heatmap.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    return path


def chart_trending_timeline(df: pd.DataFrame) -> Path:
    recent = df[df["days_since"] <= 14].copy()
    if recent.empty:
        recent = df.nlargest(15, "views_per_day").copy()

    recent = recent.sort_values("published_at")
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.scatter(
        recent["published_at"].dt.date,
        recent["views_per_day"],
        color=PALETTE,
        s=80,
        zorder=5,
    )
    ax.plot(
        recent["published_at"].dt.date,
        recent["views_per_day"],
        color=PALETTE,
        alpha=0.4,
        linewidth=1,
    )
    ax.set_xlabel("Publish Date", color=TEXT_COLOR)
    ax.set_ylabel("Views per Day", color=TEXT_COLOR)
    plt.xticks(rotation=30)
    _fig_style(fig, ax, "Trending: Views per Day (Recent Videos)")
    plt.tight_layout()
    path = CHARTS_DIR / "trending_timeline.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    return path


# ── Insights builder ───────────────────────────────────────────────────────────
def build_insights(df: pd.DataFrame, channels: list[dict], keywords: list[str]) -> dict:
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    charts = {
        "top_videos_bar": str(chart_top_videos_bar(df)),
        "engagement_scatter": str(chart_engagement_scatter(df)),
        "keyword_heatmap": str(chart_keyword_heatmap(df, keywords)),
        "trending_timeline": str(chart_trending_timeline(df)),
    }
    print("  Charts generated.")

    def video_row(row):
        return {
            "video_id": row["video_id"],
            "title": row["title"],
            "channel": row["channel_title"],
            "published_at": str(row["published_at"].date()) if pd.notna(row["published_at"]) else "",
            "view_count": int(row["view_count"]),
            "like_count": int(row["like_count"]),
            "comment_count": int(row["comment_count"]),
            "engagement_rate": round(float(row["engagement_rate"]), 2),
            "views_per_day": round(float(row["views_per_day"]), 1),
            "keywords_matched": row["keywords_matched"],
        }

    top_by_views = [video_row(r) for _, r in df.nlargest(10, "view_count").iterrows()]
    top_by_engagement = [video_row(r) for _, r in df.nlargest(10, "engagement_rate").iterrows()]
    trending_recent = [
        video_row(r) for _, r in df[df["days_since"] <= 14].nlargest(10, "views_per_day").iterrows()
    ]
    if not trending_recent:
        trending_recent = [video_row(r) for _, r in df.nlargest(10, "views_per_day").iterrows()]

    # Keyword performance
    keyword_performance = {}
    for kw in keywords:
        kw_df = df[df["keywords_matched"].apply(lambda x: kw in x)]
        keyword_performance[kw] = {
            "video_count": len(kw_df),
            "avg_views": int(kw_df["view_count"].mean()) if len(kw_df) else 0,
            "avg_engagement_rate": round(float(kw_df["engagement_rate"].mean()), 2) if len(kw_df) else 0,
            "total_views": int(kw_df["view_count"].sum()),
        }

    # Popular tags
    all_tags = []
    for tags in df["tags"]:
        if isinstance(tags, list):
            all_tags.extend([t.lower() for t in tags])
    popular_tags = [{"tag": t, "count": c} for t, c in Counter(all_tags).most_common(20)]

    # Channel ranking by subscribers
    ch_df = pd.DataFrame(channels).sort_values("subscriber_count", ascending=False)
    top_channels = [
        {
            "channel_id": r["channel_id"],
            "channel_title": r["channel_title"],
            "subscriber_count": int(r["subscriber_count"]),
            "video_count": int(r["video_count"]),
            "total_views": int(r["view_count"]),
        }
        for _, r in ch_df.head(10).iterrows()
    ]

    # Summary
    summary = {
        "total_videos_analyzed": len(df),
        "total_channels": len(channels),
        "avg_view_count": int(df["view_count"].mean()),
        "avg_engagement_rate": round(float(df["engagement_rate"].mean()), 2),
        "total_views_analyzed": int(df["view_count"].sum()),
        "date_range_days": int(df["days_since"].max()),
        "top_keyword_by_views": max(keyword_performance, key=lambda k: keyword_performance[k]["avg_views"]),
    }

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "top_videos_by_views": top_by_views,
        "top_videos_by_engagement": top_by_engagement,
        "trending_recent": trending_recent,
        "top_channels": top_channels,
        "keyword_performance": keyword_performance,
        "popular_tags": popular_tags,
        "charts": charts,
    }


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"{INPUT_PATH} not found. Run fetch_youtube_data.py first.")

    raw = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    videos = raw["videos"]
    channels = raw["channels"]
    keywords = raw["keywords"]

    print(f"Loaded {len(videos)} videos, {len(channels)} channels")

    df = pd.DataFrame(videos)
    df = compute_video_metrics(df)

    print("Computing insights and generating charts...")
    insights = build_insights(df, channels, keywords)

    OUTPUT_PATH.write_text(json.dumps(insights, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone. Insights saved to {OUTPUT_PATH}")
    print(f"  Total videos: {insights['summary']['total_videos_analyzed']}")
    print(f"  Avg engagement rate: {insights['summary']['avg_engagement_rate']}%")
    print(f"  Top keyword by avg views: {insights['summary']['top_keyword_by_views']}")
    print(f"  Charts saved to {CHARTS_DIR}/")


if __name__ == "__main__":
    main()
