"""
create_insight_deck.py
Step 3 of the YouTube Content Insights workflow.
Reads .tmp/youtube_insights.json + chart PNGs, builds an 8-slide .pptx report.
"""

import json
from datetime import datetime
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

INPUT_PATH = Path(".tmp/youtube_insights.json")
OUTPUT_PATH = Path(".tmp/youtube_insights_report.pptx")

# ── Design tokens ──────────────────────────────────────────────────────────────
BG_DARK = RGBColor(0x0D, 0x1B, 0x2A)
BG_CARD = RGBColor(0x14, 0x2A, 0x40)
GOLD = RGBColor(0xF5, 0xC5, 0x18)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREY = RGBColor(0xA0, 0xB0, 0xC0)
RED_ACCENT = RGBColor(0xE5, 0x3E, 0x3E)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)


# ── Low-level helpers ──────────────────────────────────────────────────────────
def _fill_slide(slide, color: RGBColor):
    from pptx.oxml.ns import qn
    from lxml import etree

    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_text(slide, text: str, left, top, width, height,
              font_size=18, bold=False, color=WHITE, align=PP_ALIGN.LEFT, italic=False):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    return txBox


def _add_rect(slide, left, top, width, height, fill_color: RGBColor, line_color=None):
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height,
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
    else:
        shape.line.fill.background()
    return shape


def _add_image(slide, path: str, left, top, width, height):
    if Path(path).exists():
        slide.shapes.add_picture(path, left, top, width, height)


def _number(n) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


# ── Slide builders ─────────────────────────────────────────────────────────────
def add_cover_slide(prs: Presentation, insights: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    _fill_slide(slide, BG_DARK)

    # Gold accent bar
    _add_rect(slide, Inches(0), Inches(3.0), SLIDE_W, Inches(0.06), GOLD)

    _add_text(slide, "YouTube Content Insights",
              Inches(1.2), Inches(1.5), Inches(10), Inches(1.2),
              font_size=42, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    _add_text(slide, "Tailored Clothing & Custom T-Shirts Niche",
              Inches(1.2), Inches(2.7), Inches(10), Inches(0.7),
              font_size=22, color=GOLD, align=PP_ALIGN.CENTER)

    date_str = datetime.now().strftime("%B %d, %Y")
    _add_text(slide, f"Market Analysis Report  ·  {date_str}",
              Inches(1.2), Inches(3.3), Inches(10), Inches(0.6),
              font_size=14, color=GREY, align=PP_ALIGN.CENTER, italic=True)

    summary = insights["summary"]
    stats = [
        (f"{summary['total_videos_analyzed']}", "Videos Analyzed"),
        (f"{summary['total_channels']}", "Channels"),
        (f"{_number(summary['total_views_analyzed'])}", "Total Views"),
        (f"{summary['avg_engagement_rate']}%", "Avg Engagement"),
    ]
    card_w = Inches(2.4)
    card_h = Inches(1.3)
    start_x = Inches(1.1)
    for i, (val, label) in enumerate(stats):
        x = start_x + i * Inches(2.9)
        _add_rect(slide, x, Inches(5.0), card_w, card_h, BG_CARD, GOLD)
        _add_text(slide, val, x, Inches(5.1), card_w, Inches(0.6),
                  font_size=24, bold=True, color=GOLD, align=PP_ALIGN.CENTER)
        _add_text(slide, label, x, Inches(5.7), card_w, Inches(0.4),
                  font_size=10, color=GREY, align=PP_ALIGN.CENTER)


def add_executive_summary(prs: Presentation, insights: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _fill_slide(slide, BG_DARK)
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.0), BG_CARD)
    _add_text(slide, "Executive Summary",
              Inches(0.4), Inches(0.15), Inches(12), Inches(0.7),
              font_size=28, bold=True, color=GOLD)

    s = insights["summary"]
    kw = s.get("top_keyword_by_views", "N/A")
    kp = insights["keyword_performance"]
    best_kw_views = kp.get(kw, {}).get("avg_views", 0)

    bullets = [
        f"Analyzed {s['total_videos_analyzed']} videos across {s['total_channels']} unique channels in the last {s['date_range_days']} days",
        f"Combined total of {_number(s['total_views_analyzed'])} views across all analyzed content",
        f"Average engagement rate: {s['avg_engagement_rate']}% (likes + comments / views)",
        f"Best-performing keyword: \"{kw}\" averaging {_number(best_kw_views)} views per video",
        f"See slides 3–8 for deep-dives on top videos, engagement, keyword breakdown, and channel landscape",
    ]

    for i, bullet in enumerate(bullets):
        y = Inches(1.3) + i * Inches(1.0)
        _add_rect(slide, Inches(0.3), y, Inches(12.5), Inches(0.8), BG_CARD)
        _add_text(slide, f"→  {bullet}", Inches(0.5), y + Inches(0.1),
                  Inches(12.1), Inches(0.6), font_size=14, color=WHITE)


def add_top_videos_table(prs: Presentation, insights: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _fill_slide(slide, BG_DARK)
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.0), BG_CARD)
    _add_text(slide, "Top 10 Videos by View Count",
              Inches(0.4), Inches(0.15), Inches(12), Inches(0.7),
              font_size=28, bold=True, color=GOLD)

    headers = ["#", "Title", "Channel", "Views", "Eng %"]
    col_widths = [Inches(0.4), Inches(5.8), Inches(2.8), Inches(1.3), Inches(1.0)]
    col_x = [Inches(0.3)]
    for w in col_widths[:-1]:
        col_x.append(col_x[-1] + w)

    row_h = Inches(0.52)
    header_y = Inches(1.05)

    _add_rect(slide, Inches(0.3), header_y, Inches(11.5), row_h, GOLD)
    for j, (h, x, w) in enumerate(zip(headers, col_x, col_widths)):
        _add_text(slide, h, x + Inches(0.05), header_y + Inches(0.07),
                  w, row_h, font_size=11, bold=True, color=BG_DARK)

    for i, v in enumerate(insights["top_videos_by_views"][:10]):
        y = header_y + (i + 1) * row_h
        row_color = BG_CARD if i % 2 == 0 else BG_DARK
        _add_rect(slide, Inches(0.3), y, Inches(11.5), row_h, row_color)
        cells = [
            str(i + 1),
            v["title"][:55] + ("…" if len(v["title"]) > 55 else ""),
            v["channel"][:30],
            _number(v["view_count"]),
            f"{v['engagement_rate']}%",
        ]
        for cell, x, w in zip(cells, col_x, col_widths):
            _add_text(slide, cell, x + Inches(0.05), y + Inches(0.08),
                      w, row_h, font_size=10, color=WHITE)


def add_chart_slide(prs: Presentation, title: str, subtitle: str,
                    chart_path: str, bullets: list[str]):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _fill_slide(slide, BG_DARK)
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.0), BG_CARD)
    _add_text(slide, title, Inches(0.4), Inches(0.12), Inches(12), Inches(0.75),
              font_size=26, bold=True, color=GOLD)

    # Chart left, bullets right
    _add_image(slide, chart_path, Inches(0.2), Inches(1.1), Inches(8.5), Inches(5.8))

    _add_text(slide, subtitle, Inches(8.9), Inches(1.1), Inches(4.0), Inches(0.5),
              font_size=11, color=GREY, italic=True)
    for i, b in enumerate(bullets):
        y = Inches(1.7) + i * Inches(0.85)
        _add_rect(slide, Inches(8.9), y, Inches(4.0), Inches(0.75), BG_CARD)
        _add_text(slide, b, Inches(9.0), y + Inches(0.08), Inches(3.8), Inches(0.65),
                  font_size=10, color=WHITE)


def add_top_channels(prs: Presentation, insights: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _fill_slide(slide, BG_DARK)
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.0), BG_CARD)
    _add_text(slide, "Top Channels in the Niche",
              Inches(0.4), Inches(0.15), Inches(12), Inches(0.7),
              font_size=28, bold=True, color=GOLD)

    headers = ["#", "Channel", "Subscribers", "Total Views", "Videos"]
    col_widths = [Inches(0.4), Inches(4.5), Inches(2.2), Inches(2.2), Inches(1.5)]
    col_x = [Inches(0.5)]
    for w in col_widths[:-1]:
        col_x.append(col_x[-1] + w)

    row_h = Inches(0.52)
    header_y = Inches(1.05)
    _add_rect(slide, Inches(0.5), header_y, Inches(10.8), row_h, GOLD)
    for h, x, w in zip(headers, col_x, col_widths):
        _add_text(slide, h, x + Inches(0.05), header_y + Inches(0.07),
                  w, row_h, font_size=11, bold=True, color=BG_DARK)

    for i, ch in enumerate(insights["top_channels"][:10]):
        y = header_y + (i + 1) * row_h
        row_color = BG_CARD if i % 2 == 0 else BG_DARK
        _add_rect(slide, Inches(0.5), y, Inches(10.8), row_h, row_color)
        cells = [
            str(i + 1),
            ch["channel_title"][:40],
            _number(ch["subscriber_count"]),
            _number(ch["total_views"]),
            str(ch["video_count"]),
        ]
        for cell, x, w in zip(cells, col_x, col_widths):
            _add_text(slide, cell, x + Inches(0.05), y + Inches(0.08),
                      w, row_h, font_size=10, color=WHITE)


def add_recommendations(prs: Presentation, insights: dict):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _fill_slide(slide, BG_DARK)
    _add_rect(slide, Inches(0), Inches(0), SLIDE_W, Inches(1.0), BG_CARD)
    _add_text(slide, "Trending Now & Content Recommendations",
              Inches(0.4), Inches(0.12), Inches(12.5), Inches(0.75),
              font_size=26, bold=True, color=GOLD)

    # Chart on the left
    chart_path = insights["charts"].get("trending_timeline", "")
    _add_image(slide, chart_path, Inches(0.2), Inches(1.1), Inches(7.0), Inches(5.5))

    # Recommendations on right
    s = insights["summary"]
    kp = insights["keyword_performance"]
    tags = [t["tag"] for t in insights["popular_tags"][:5]]
    best_kw = s.get("top_keyword_by_views", "")
    trending = insights["trending_recent"][:3]

    recs = [
        f"Focus on \"{best_kw}\" — highest avg view count of all keywords",
        f"Trending tags to use: {', '.join(tags)}",
        "Engagement is driven by how-to / tutorial style content — focus on showing the process",
        "Target 7–12 min videos — sweet spot for fashion/menswear educational content",
        f"Study top channel: {insights['top_channels'][0]['channel_title'] if insights['top_channels'] else 'N/A'}",
    ]

    _add_text(slide, "Action Items", Inches(7.5), Inches(1.1), Inches(5.5), Inches(0.45),
              font_size=14, bold=True, color=GOLD)
    for i, rec in enumerate(recs):
        y = Inches(1.6) + i * Inches(0.95)
        _add_rect(slide, Inches(7.5), y, Inches(5.5), Inches(0.85), BG_CARD, GOLD)
        _add_text(slide, f"{i + 1}.  {rec}", Inches(7.65), y + Inches(0.08),
                  Inches(5.2), Inches(0.75), font_size=10, color=WHITE)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"{INPUT_PATH} not found. Run analyze_insights.py first.")

    insights = json.loads(INPUT_PATH.read_text(encoding="utf-8"))

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    charts = insights["charts"]

    print("Building slides...")
    add_cover_slide(prs, insights)
    print("  1/8 Cover")

    add_executive_summary(prs, insights)
    print("  2/8 Executive Summary")

    add_top_videos_table(prs, insights)
    print("  3/8 Top Videos Table")

    add_chart_slide(
        prs,
        "Top Performing Content",
        "View count leaders — what's capturing attention",
        charts.get("top_videos_bar", ""),
        [
            "Top videos dominate with tutorial/review format",
            "Channels with consistent uploads outperform",
            "High views correlate with keyword-rich titles",
        ],
    )
    print("  4/8 Top Content Chart")

    add_chart_slide(
        prs,
        "Engagement Analysis",
        "Engagement rate = (likes + comments) / views",
        charts.get("engagement_scatter", ""),
        [
            "High engagement outliers have niche audiences",
            "Low view count ≠ low engagement",
            "Target 2–5% engagement as a benchmark",
        ],
    )
    print("  5/8 Engagement Chart")

    add_chart_slide(
        prs,
        "Keyword Performance",
        "Which search terms drive views and engagement",
        charts.get("keyword_heatmap", ""),
        [
            "Compare avg views vs video count per keyword",
            "Low competition keywords = easier wins",
            "Combine top keywords in titles for reach",
        ],
    )
    print("  6/8 Keyword Heatmap")

    add_top_channels(prs, insights)
    print("  7/8 Top Channels")

    add_recommendations(prs, insights)
    print("  8/8 Recommendations")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUTPUT_PATH)
    print(f"\nDone. Deck saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
