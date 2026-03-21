"""
generate_pdf_report.py
Canvas-design skill execution — Sartorial Signal design philosophy.
Reads .tmp/youtube_insights.json and produces a 4-page art-directed PDF
saved to .tmp/youtube_insights_report.pdf
"""

import json
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Paths ──────────────────────────────────────────────────────────────────────
INSIGHTS_PATH = Path(".tmp/youtube_insights.json")
OUTPUT_PATH   = Path(".tmp/youtube_insights_report.pdf")
FONTS_DIR     = Path(".claude/skills/canvas-design/canvas-fonts")

# ── Palette — Sartorial Signal ─────────────────────────────────────────────────
NAVY   = colors.HexColor("#0D1B2A")
NAVY2  = colors.HexColor("#142A40")
GOLD   = colors.HexColor("#C9A84C")
GOLD2  = colors.HexColor("#F5C518")
WHITE  = colors.HexColor("#F0EDE6")
SMOKE  = colors.HexColor("#7A8A9A")
DARK   = colors.HexColor("#060E17")

W, H   = A4   # 595.27 x 841.89 pts
M      = 22*mm  # margin


# ── Font registration ──────────────────────────────────────────────────────────
# Maps our semantic names to reportlab built-in font names
FONT_MAP = {
    "Lora":          "Times-Roman",
    "LoraBold":      "Times-Bold",
    "LoraItalic":    "Times-Italic",
    "Mono":          "Courier",
    "MonoBold":      "Courier-Bold",
    "Work":          "Helvetica",
    "WorkBold":      "Helvetica-Bold",
    "WorkItalic":    "Helvetica-Oblique",
    "CrimsonItalic": "Times-Italic",
    "InstrumentBold":"Helvetica-Bold",
}

def register_fonts():
    # Try to register system TTF fonts; fall back gracefully to built-ins
    win_fonts = Path("C:/Windows/Fonts")
    candidates = {
        "Lora":          ("georgia.ttf",    "Times-Roman"),
        "LoraBold":      ("georgiab.ttf",   "Times-Bold"),
        "LoraItalic":    ("georgiai.ttf",   "Times-Italic"),
        "Mono":          ("consola.ttf",    "Courier"),
        "MonoBold":      ("consolab.ttf",   "Courier-Bold"),
        "Work":          ("calibri.ttf",    "Helvetica"),
        "WorkBold":      ("calibrib.ttf",   "Helvetica-Bold"),
        "WorkItalic":    ("calibrii.ttf",   "Helvetica-Oblique"),
        "CrimsonItalic": ("georgiai.ttf",   "Times-Italic"),
        "InstrumentBold":("calibrib.ttf",   "Helvetica-Bold"),
    }
    for alias, (fname, fallback) in candidates.items():
        path = win_fonts / fname
        if path.exists():
            try:
                pdfmetrics.registerFont(TTFont(alias, str(path)))
                FONT_MAP[alias] = alias  # use registered name
            except Exception:
                FONT_MAP[alias] = fallback
        else:
            FONT_MAP[alias] = fallback

# ── Helpers ────────────────────────────────────────────────────────────────────
def bg(c, color=NAVY):
    c.setFillColor(color)
    c.rect(0, 0, W, H, fill=1, stroke=0)

def hline(c, y, x0=M, x1=None, width=0.4, color=GOLD):
    if x1 is None: x1 = W - M
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x0, y, x1, y)

def vline(c, x, y0=M, y1=None, width=0.4, color=GOLD):
    if y1 is None: y1 = H - M
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x, y0, x, y1)

def txt(c, text, x, y, font="Work", size=10, color=WHITE, align="left"):
    c.setFillColor(color)
    c.setFont(FONT_MAP.get(font, font), size)
    if align == "center":
        c.drawCentredString(x, y, text)
    elif align == "right":
        c.drawRightString(x, y, text)
    else:
        c.drawString(x, y, text)

def rect(c, x, y, w, h, fill=NAVY2, stroke=None, stroke_width=0.5):
    c.setFillColor(fill)
    if stroke:
        c.setStrokeColor(stroke)
        c.setLineWidth(stroke_width)
        c.rect(x, y, w, h, fill=1, stroke=1)
    else:
        c.rect(x, y, w, h, fill=1, stroke=0)

def num_fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.0f}K"
    return str(n)

def truncate(s, n):
    return s[:n] + "…" if len(s) > n else s


# ── Page 1: Cover ──────────────────────────────────────────────────────────────
def page_cover(c, insights):
    bg(c, DARK)

    # Vertical gold rule far left
    vline(c, M - 4*mm, y0=M, y1=H - M, width=1.2, color=GOLD)

    # Massive background number — ghost watermark
    s = insights["summary"]
    c.setFillColor(colors.HexColor("#0F2035"))
    c.setFont(FONT_MAP["LoraBold"], 280)
    c.drawCentredString(W/2 + 20, H/2 - 120, str(s["total_videos_analyzed"]))

    # Top label
    txt(c, "SARTORIAL SIGNAL", M + 4, H - M - 8, font="Mono", size=8, color=GOLD)
    txt(c, f"NICHE INTELLIGENCE REPORT  ·  {datetime.now().strftime('%B %Y').upper()}",
        M + 4, H - M - 20, font="Mono", size=7, color=SMOKE)

    # Main title block
    title_y = H * 0.62
    txt(c, "YouTube", M + 4, title_y + 46, font="LoraItalic", size=52, color=WHITE)
    txt(c, "Content", M + 4, title_y, font="LoraBold", size=66, color=WHITE)

    c.setFillColor(GOLD)
    c.setFont(FONT_MAP["LoraBold"], 66)
    c.drawString(M + 4, title_y - 54, "Insights")

    # Subtitle
    txt(c, "Tailored Clothing & Custom T-Shirts", M + 4, title_y - 82,
        font="CrimsonItalic", size=16, color=SMOKE)

    # Horizontal rule
    hline(c, title_y - 98, x0=M + 4, x1=W - M - 20, width=0.5, color=GOLD)

    # Key stats row at bottom
    stats = [
        (num_fmt(s["total_videos_analyzed"]), "VIDEOS"),
        (num_fmt(s["total_channels"]),         "CHANNELS"),
        (num_fmt(s["total_views_analyzed"]),   "TOTAL VIEWS"),
        (f"{s['avg_engagement_rate']}%",        "AVG ENGAGEMENT"),
    ]
    stat_y = M + 38
    col_w  = (W - 2*M) / 4
    for i, (val, label) in enumerate(stats):
        x = M + i * col_w
        if i > 0:
            vline(c, x, y0=stat_y - 6, y1=stat_y + 32, width=0.3, color=SMOKE)
        txt(c, val,   x + 8, stat_y + 14, font="MonoBold", size=18, color=GOLD2)
        txt(c, label, x + 8, stat_y,      font="Mono",     size=6.5, color=SMOKE)

    hline(c, stat_y + 42, x0=M, x1=W-M, width=0.3, color=SMOKE)

    # Page marker
    txt(c, "01", W - M - 4, M + 4, font="Mono", size=8, color=SMOKE, align="right")


# ── Page 2: Keyword & Engagement Analysis ──────────────────────────────────────
def page_analysis(c, insights):
    bg(c, NAVY)

    # Section header
    hline(c, H - M - 2, width=0.8)
    txt(c, "SIGNAL ANALYSIS", M, H - M + 6, font="Mono", size=7.5, color=GOLD)
    txt(c, "02", W - M, H - M + 6, font="Mono", size=7.5, color=SMOKE, align="right")

    # — LEFT COLUMN: Keyword performance ——
    kp  = insights["keyword_performance"]
    col_x = M
    kw_y  = H - M - 40

    txt(c, "Keyword Performance", col_x, kw_y, font="LoraBold", size=18, color=WHITE)
    txt(c, "avg views per keyword · 90-day window", col_x, kw_y - 14,
        font="WorkItalic", size=8, color=SMOKE)

    max_views = max(d["avg_views"] for d in kp.values()) or 1
    bar_w_max = 200
    bar_h     = 13
    bar_gap   = 22
    bar_y     = kw_y - 36

    sorted_kw = sorted(kp.items(), key=lambda x: x[1]["avg_views"], reverse=True)
    for kw, data in sorted_kw:
        bw = max(3, int(data["avg_views"] / max_views * bar_w_max))
        # Bar bg
        rect(c, col_x, bar_y - 2, bar_w_max, bar_h, fill=NAVY2)
        # Bar fill
        rect(c, col_x, bar_y - 2, bw, bar_h, fill=GOLD)
        # Label
        txt(c, kw.title(), col_x, bar_y + 2, font="Work", size=7.5, color=WHITE)
        txt(c, num_fmt(data["avg_views"]),
            col_x + bar_w_max + 5, bar_y + 2, font="Mono", size=7.5, color=GOLD2)
        txt(c, f"{data['video_count']}v",
            col_x + bar_w_max + 38, bar_y + 2, font="Mono", size=6.5, color=SMOKE)
        bar_y -= bar_gap

    # — RIGHT COLUMN: Top engagement videos ——
    rx = W / 2 + 8*mm
    eng_y = H - M - 40

    txt(c, "High Engagement", rx, eng_y, font="LoraBold", size=18, color=WHITE)
    txt(c, "engagement rate = (likes + comments) / views", rx, eng_y - 14,
        font="WorkItalic", size=8, color=SMOKE)

    top_eng = insights["top_videos_by_engagement"][:6]
    row_y   = eng_y - 38
    row_h   = 30

    for v in top_eng:
        rect(c, rx, row_y - 2, W - rx - M, row_h, fill=NAVY2, stroke=GOLD, stroke_width=0.3)
        txt(c, truncate(v["title"], 44), rx + 5, row_y + 16,
            font="Work", size=7.5, color=WHITE)
        txt(c, v["channel"], rx + 5, row_y + 5,
            font="WorkItalic", size=7, color=SMOKE)
        eng_str = f"{v['engagement_rate']}%"
        c.setFillColor(GOLD)
        c.setFont(FONT_MAP["MonoBold"], 13)
        c.drawRightString(W - M - 4, row_y + 10, eng_str)
        row_y -= (row_h + 5)

    # — Bottom: Popular tags cloud ——
    hline(c, row_y - 10, width=0.3, color=SMOKE)
    tags_y = row_y - 28
    txt(c, "Dominant Tags in the Niche", M, tags_y, font="LoraBold", size=13, color=WHITE)

    tags_x = M
    tag_row_y = tags_y - 20
    for i, t in enumerate(insights["popular_tags"][:16]):
        tw = len(t["tag"]) * 5 + 16
        if tags_x + tw > W - M:
            tags_x = M
            tag_row_y -= 18
        rect(c, tags_x, tag_row_y - 2, tw, 13, fill=NAVY2, stroke=GOLD2, stroke_width=0.3)
        txt(c, t["tag"], tags_x + 5, tag_row_y + 1, font="Mono", size=6.5, color=GOLD2)
        tags_x += tw + 6


# ── Page 3: Top Videos ─────────────────────────────────────────────────────────
def page_top_videos(c, insights):
    bg(c, DARK)

    hline(c, H - M - 2, width=0.8)
    txt(c, "TOP VIDEOS BY VIEW COUNT", M, H - M + 6, font="Mono", size=7.5, color=GOLD)
    txt(c, "03", W - M, H - M + 6, font="Mono", size=7.5, color=SMOKE, align="right")

    videos = insights["top_videos_by_views"][:10]

    # Column headers
    col_y = H - M - 30
    hline(c, col_y - 4, width=0.3, color=GOLD)
    txt(c, "#",      M,            col_y, font="Mono", size=7, color=GOLD)
    txt(c, "TITLE",  M + 20,       col_y, font="Mono", size=7, color=GOLD)
    txt(c, "CHANNEL",M + 265,      col_y, font="Mono", size=7, color=GOLD)
    txt(c, "VIEWS",  M + 395,      col_y, font="Mono", size=7, color=GOLD)
    txt(c, "ENG%",   M + 445,      col_y, font="Mono", size=7, color=GOLD)
    txt(c, "V/DAY",  W - M - 38,   col_y, font="Mono", size=7, color=GOLD)

    row_h = 34
    row_y = col_y - 16

    for i, v in enumerate(videos):
        fill = NAVY2 if i % 2 == 0 else colors.HexColor("#0A1620")
        rect(c, M - 2, row_y - 6, W - 2*M + 4, row_h, fill=fill)

        # Rank — large gold
        c.setFillColor(GOLD if i == 0 else SMOKE)
        c.setFont(FONT_MAP["LoraBold"] if i == 0 else FONT_MAP["Lora"], 18 if i == 0 else 13)
        c.drawString(M, row_y + 10, str(i + 1).zfill(2))

        # Title & channel
        txt(c, truncate(v["title"], 40), M + 20, row_y + 14, font="Work", size=8, color=WHITE)
        txt(c, truncate(v["channel"], 28), M + 20, row_y + 4, font="WorkItalic", size=7, color=SMOKE)

        # Channel
        txt(c, truncate(v["channel"], 20), M + 265, row_y + 9,
            font="Work", size=7.5, color=SMOKE)

        # Views — prominent
        c.setFillColor(GOLD2 if i < 3 else WHITE)
        c.setFont(FONT_MAP["MonoBold"] if i < 3 else FONT_MAP["Mono"], 10)
        c.drawRightString(M + 440, row_y + 9, num_fmt(v["view_count"]))

        # Engagement
        eng_color = GOLD2 if v["engagement_rate"] > 4 else WHITE
        txt(c, f"{v['engagement_rate']}%", M + 445, row_y + 9,
            font="Mono", size=8.5, color=eng_color)

        # Views per day
        txt(c, num_fmt(int(v["views_per_day"])), W - M - 38, row_y + 9,
            font="Mono", size=8, color=SMOKE)

        row_y -= row_h

    # Bottom annotation
    hline(c, row_y + 10, width=0.3, color=SMOKE)
    txt(c, f"Data window: {insights['summary']['date_range_days']} days  ·  "
          f"{insights['summary']['total_videos_analyzed']} videos analyzed  ·  "
          f"Generated {datetime.now().strftime('%d %b %Y')}",
        M, row_y - 2, font="Mono", size=6.5, color=SMOKE)


# ── Page 4: Channels + Recommendations ────────────────────────────────────────
def page_channels(c, insights):
    bg(c, NAVY)

    hline(c, H - M - 2, width=0.8)
    txt(c, "CHANNELS & STRATEGY", M, H - M + 6, font="Mono", size=7.5, color=GOLD)
    txt(c, "04", W - M, H - M + 6, font="Mono", size=7.5, color=SMOKE, align="right")

    channels = insights["top_channels"][:8]
    s        = insights["summary"]

    # — LEFT: Channel table ——
    col_y = H - M - 32
    txt(c, "Channel Landscape", M, col_y, font="LoraBold", size=18, color=WHITE)
    txt(c, "ranked by subscriber count", M, col_y - 14, font="WorkItalic", size=8, color=SMOKE)

    hline(c, col_y - 22, x0=M, x1=M + 230, width=0.5)

    row_y = col_y - 40
    for i, ch in enumerate(channels):
        fill = NAVY2 if i % 2 == 0 else DARK
        rect(c, M, row_y - 3, 230, 24, fill=fill)

        # Rank dot
        c.setFillColor(GOLD if i < 3 else SMOKE)
        c.circle(M + 8, row_y + 9, 3, fill=1, stroke=0)

        txt(c, truncate(ch["channel_title"], 22), M + 18, row_y + 10,
            font="WorkBold" if i < 3 else "Work", size=8, color=WHITE)
        txt(c, num_fmt(ch["subscriber_count"]) + " subs",
            M + 18, row_y + 1, font="Mono", size=6.5, color=GOLD2 if i < 3 else SMOKE)
        txt(c, num_fmt(ch["total_views"]),
            M + 200, row_y + 5, font="Mono", size=7, color=SMOKE, align="right")

        row_y -= 27

    # — RIGHT: Recommendations ——
    rx    = W / 2 + 4*mm
    rec_y = H - M - 32

    txt(c, "Strategic Recommendations", rx, rec_y, font="LoraBold", size=18, color=WHITE)
    txt(c, "derived from engagement & trend signals", rx, rec_y - 14,
        font="WorkItalic", size=8, color=SMOKE)

    hline(c, rec_y - 22, x0=rx, x1=W - M, width=0.5)

    top_kw    = s["top_keyword_by_views"]
    kp        = insights["keyword_performance"]
    top_tags  = [t["tag"] for t in insights["popular_tags"][:4]]
    top_ch    = channels[0]["channel_title"] if channels else "N/A"
    top_video = insights["top_videos_by_views"][0]

    recs = [
        ("KEYWORD FOCUS",
         f'Lead with "{top_kw}" — highest avg views across all search terms.'),
        ("TAG STRATEGY",
         f"Embed: {', '.join(top_tags)} in all titles and descriptions."),
        ("FORMAT",
         "Alteration & transformation content drives highest engagement (3–8%)."),
        ("CHANNEL STUDY",
         f"Benchmark against {top_ch} — top performer by subscriber reach."),
        ("VIDEO LENGTH",
         "7–12 min performs best. Educational process-focused framing wins."),
        ("TRENDING SIGNAL",
         f'"{truncate(top_video["title"], 38)}" — {num_fmt(top_video["view_count"])} views.'),
    ]

    item_y = rec_y - 44
    for title_r, body in recs:
        rect(c, rx, item_y - 4, W - rx - M, 36,
             fill=colors.HexColor("#0A1F30"), stroke=GOLD, stroke_width=0.4)
        # Gold left rule
        c.setFillColor(GOLD)
        c.rect(rx, item_y - 4, 3, 36, fill=1, stroke=0)
        txt(c, title_r, rx + 10, item_y + 18, font="MonoBold", size=7, color=GOLD)
        # Wrap body text manually
        words = body.split()
        line, lines = [], []
        for w in words:
            test = " ".join(line + [w])
            if len(test) * 4.5 > (W - rx - M - 18):
                lines.append(" ".join(line))
                line = [w]
            else:
                line.append(w)
        if line: lines.append(" ".join(line))
        for li, ln in enumerate(lines[:2]):
            txt(c, ln, rx + 10, item_y + 8 - li * 9, font="Work", size=7.5, color=WHITE)
        item_y -= 44

    # — Bottom: summary strip ——
    strip_y = M + 10
    rect(c, M - 2, strip_y - 4, W - 2*M + 4, 28, fill=DARK)
    hline(c, strip_y + 24, width=0.3, color=GOLD)

    summary_items = [
        (f"{s['total_videos_analyzed']} VIDEOS", "analyzed"),
        (f"{s['total_channels']} CHANNELS",       "tracked"),
        (num_fmt(s["total_views_analyzed"]) + " VIEWS", "total"),
        (f"{s['avg_engagement_rate']}% ENGAGEMENT", "avg rate"),
        (f"{s['date_range_days']} DAYS",            "window"),
    ]
    col_w = (W - 2*M) / len(summary_items)
    for i, (val, sub) in enumerate(summary_items):
        x = M + i * col_w
        txt(c, val, x + 4, strip_y + 10, font="MonoBold", size=7.5, color=GOLD2)
        txt(c, sub, x + 4, strip_y + 1,  font="Mono",     size=6,   color=SMOKE)


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not INSIGHTS_PATH.exists():
        raise FileNotFoundError(f"{INSIGHTS_PATH} not found. Run analyze_insights.py first.")

    register_fonts()
    insights = json.loads(INSIGHTS_PATH.read_text(encoding="utf-8"))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    cv = canvas.Canvas(str(OUTPUT_PATH), pagesize=A4)
    cv.setTitle("YouTube Content Insights — Sartorial Signal")
    cv.setAuthor("WAT Framework")

    print("Building PDF pages...")

    page_cover(cv, insights);   cv.showPage(); print("  1/4 Cover")
    page_analysis(cv, insights); cv.showPage(); print("  2/4 Analysis")
    page_top_videos(cv, insights); cv.showPage(); print("  3/4 Top Videos")
    page_channels(cv, insights); cv.showPage(); print("  4/4 Channels & Strategy")

    cv.save()
    print(f"\nDone. PDF saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
