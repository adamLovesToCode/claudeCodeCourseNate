"""
generate_pdf.py

Generates a formatted PDF competitor analysis report from analysis.json.

Outputs: .tmp/competitor_analysis_{timestamp}.pdf
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from fpdf import FPDF

load_dotenv()

ANALYSIS_PATH = ".tmp/analysis.json"
BUSINESS_INFO_PATH = "business_info/business_info.json"
OUTPUT_DIR = ".tmp"

# Colors (R, G, B)
COLOR_PRIMARY = (30, 80, 160)       # Blue — headers
COLOR_STRENGTH = (34, 139, 34)      # Green — strengths
COLOR_WEAKNESS = (178, 34, 34)      # Red — weaknesses
COLOR_HIGH = (220, 53, 69)          # Red — high priority
COLOR_MEDIUM = (200, 140, 0)        # Amber — medium priority
COLOR_LOW = (40, 167, 69)           # Green — low priority
COLOR_TABLE_HEADER = (220, 225, 240)
COLOR_SHADED = (245, 247, 250)
COLOR_TEXT = (30, 30, 30)
COLOR_SUBTEXT = (100, 100, 100)

MATRIX_YES = "Yes"
MATRIX_NO = "No"
MATRIX_PARTIAL = "Partial"
MATRIX_UNKNOWN = "?"


class CompetitorReport(FPDF):
    def __init__(self, business_name: str):
        super().__init__()
        self.business_name = business_name
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLOR_SUBTEXT)
        self.cell(0, 6, f"{self.business_name} — Competitor Analysis Report", align="L")
        self.set_text_color(*COLOR_TEXT)
        self.ln(2)
        self.set_draw_color(*COLOR_PRIMARY)
        self.set_line_width(0.3)
        self.line(20, self.get_y(), 190, self.get_y())
        self.ln(4)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLOR_SUBTEXT)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")
        self.set_text_color(*COLOR_TEXT)

    def add_cover_page(self, business_info: dict):
        self.add_page()
        self.set_fill_color(*COLOR_PRIMARY)
        self.rect(0, 0, 210, 80, "F")

        self.set_y(25)
        self.set_font("Helvetica", "B", 28)
        self.set_text_color(255, 255, 255)
        self.cell(0, 12, "Competitor Analysis Report", align="C", new_y="NEXT", new_x="LMARGIN")

        name = business_info.get("company_name", "Your Business")
        self.set_font("Helvetica", "", 16)
        self.cell(0, 10, name, align="C", new_y="NEXT", new_x="LMARGIN")

        self.set_y(90)
        self.set_text_color(*COLOR_TEXT)
        self.set_font("Helvetica", "I", 12)
        tagline = business_info.get("tagline", "")
        self.cell(0, 8, tagline, align="C", new_y="NEXT", new_x="LMARGIN")

        self.ln(8)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLOR_SUBTEXT)
        self.cell(0, 6, f"Generated: {datetime.now().strftime('%B %d, %Y')}", align="C")

    def section_title(self, title: str, level: int = 1):
        self.ln(6)
        if level == 1:
            self.set_font("Helvetica", "B", 16)
            self.set_text_color(*COLOR_PRIMARY)
            self.cell(0, 10, title, new_y="NEXT", new_x="LMARGIN")
            self.set_draw_color(*COLOR_PRIMARY)
            self.set_line_width(0.5)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(4)
        elif level == 2:
            self.set_font("Helvetica", "B", 13)
            self.set_text_color(*COLOR_PRIMARY)
            self.cell(0, 8, title, new_y="NEXT", new_x="LMARGIN")
            self.ln(2)
        elif level == 3:
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*COLOR_TEXT)
            self.cell(0, 7, title, new_y="NEXT", new_x="LMARGIN")
        self.set_text_color(*COLOR_TEXT)

    def body_text(self, text: str, indent: float = 0):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*COLOR_TEXT)
        self.set_x(20 + indent)
        self.multi_cell(170 - indent, 5.5, text)
        self.ln(1)

    def bullet(self, text: str, color: tuple = None, indent: float = 5):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*(color or COLOR_TEXT))
        x = 20 + indent
        self.set_x(x)
        self.cell(5, 5.5, "\u2022")
        self.set_x(x + 5)
        self.multi_cell(165 - indent, 5.5, text)
        self.set_text_color(*COLOR_TEXT)

    def shaded_box(self, content_fn, fill_color=COLOR_SHADED):
        y_start = self.get_y()
        x_start = 20
        width = 170
        # Draw after content so we know the height
        content_fn()
        y_end = self.get_y()
        # Re-draw the box behind (fpdf2 draws in order, so we use a rect before content)
        # Instead, use ln and manual spacing
        self.ln(2)

    def priority_label(self, priority: str):
        color_map = {"high": COLOR_HIGH, "medium": COLOR_MEDIUM, "low": COLOR_LOW}
        color = color_map.get(priority.lower(), COLOR_SUBTEXT)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*color)
        self.cell(25, 5, f"[{priority.upper()}]")
        self.set_text_color(*COLOR_TEXT)

    def add_business_overview(self, business_info: dict):
        self.add_page()
        self.section_title("Business Overview")

        self.body_text(business_info.get("description", ""))
        self.ln(3)

        self.section_title("Key Differentiators", level=3)
        for item in business_info.get("key_differentiators", []):
            self.bullet(item)

        self.ln(3)
        self.section_title("Target Audience", level=3)
        self.body_text(business_info.get("target_audience", ""))

        self.ln(3)
        self.section_title("Business Model", level=3)
        self.body_text(business_info.get("business_model", ""))

    def add_executive_summary(self, summary: str):
        self.add_page()
        self.section_title("Executive Summary")
        self.body_text(summary)

    def add_competitor_profile(self, profile: dict, index: int):
        self.add_page()
        name = profile.get("company_name") or profile.get("url", f"Competitor {index+1}")
        self.section_title(f"{index+1}. {name}", level=2)

        url = profile.get("url", "")
        if url:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(*COLOR_SUBTEXT)
            self.cell(0, 5, url, new_y="NEXT", new_x="LMARGIN")
            self.set_text_color(*COLOR_TEXT)
            self.ln(2)

        self.body_text(profile.get("overview", ""))

        # Target audience & measurement approach
        self.ln(2)
        self.set_font("Helvetica", "B", 10)
        self.cell(40, 5.5, "Target Audience:")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(130, 5.5, profile.get("target_audience", "N/A"))

        self.set_font("Helvetica", "B", 10)
        self.cell(40, 5.5, "Measurement Approach:")
        self.set_font("Helvetica", "", 10)
        self.multi_cell(130, 5.5, profile.get("measurement_approach", "N/A"))

        # Pricing box
        pricing = profile.get("pricing", {})
        self.ln(3)
        self.section_title("Pricing", level=3)
        self.set_fill_color(*COLOR_SHADED)
        self.set_font("Helvetica", "", 10)
        price_text = (
            f"Model: {pricing.get('model', 'N/A')}   |   "
            f"Range: {pricing.get('range', 'N/A')}   |   "
            f"{pricing.get('notes', '')}"
        )
        self.set_x(20)
        self.multi_cell(170, 6, price_text, fill=True)
        self.ln(2)

        # Key features
        features = profile.get("key_features", [])
        if features:
            self.section_title("Key Features", level=3)
            for f in features:
                self.bullet(f)
            self.ln(2)

        # Strengths & weaknesses
        strengths = profile.get("strengths", [])
        weaknesses = profile.get("weaknesses", [])

        col_w = 82
        y_before = self.get_y()

        if strengths:
            self.section_title("Strengths", level=3)
            for s in strengths:
                self.bullet(s, color=COLOR_STRENGTH)

        if weaknesses:
            self.section_title("Weaknesses", level=3)
            for w in weaknesses:
                self.bullet(w, color=COLOR_WEAKNESS)

        # Relevance badge
        relevance = profile.get("relevance_to_user", "")
        if relevance:
            self.ln(3)
            self.set_font("Helvetica", "B", 9)
            self.set_text_color(*COLOR_SUBTEXT)
            self.cell(0, 5, f"Competitive Relevance: {relevance.upper()}")
            self.set_text_color(*COLOR_TEXT)

    def add_feature_matrix(self, matrix: dict):
        self.add_page()
        self.section_title("Feature Comparison Matrix")

        dimensions = matrix.get("dimensions", [])
        user_biz = matrix.get("user_business", {})
        competitors = matrix.get("competitors", {})

        all_players = ["Your Business"] + list(competitors.keys())
        col_w = min(30, int(150 / len(all_players)))
        row_h = 7
        label_w = 170 - col_w * len(all_players)

        # Header row
        self.set_fill_color(*COLOR_TABLE_HEADER)
        self.set_font("Helvetica", "B", 8)
        self.set_x(20)
        self.cell(label_w, row_h, "Feature", border=1, fill=True)
        for player in all_players:
            display = player[:12] + ".." if len(player) > 14 else player
            self.cell(col_w, row_h, display, border=1, fill=True, align="C")
        self.ln()

        # Data rows
        for i, dim in enumerate(dimensions):
            fill = i % 2 == 0
            self.set_fill_color(248, 249, 250) if fill else self.set_fill_color(255, 255, 255)
            self.set_font("Helvetica", "", 8)
            self.set_x(20)
            # Truncate long dimension names
            label = dim[:38] + ".." if len(dim) > 40 else dim
            self.cell(label_w, row_h, label, border=1, fill=fill)

            # User's business column — highlight
            user_val = user_biz.get(dim, "?")
            self.set_fill_color(*COLOR_TABLE_HEADER)
            self.set_font("Helvetica", "B", 8)
            self.cell(col_w, row_h, str(user_val).capitalize(), border=1, fill=True, align="C")

            # Competitor columns
            self.set_font("Helvetica", "", 8)
            for comp_name in list(competitors.keys()):
                comp_data = competitors[comp_name]
                val = comp_data.get(dim, "?") if isinstance(comp_data, dict) else "?"
                self.set_fill_color(248, 249, 250) if fill else self.set_fill_color(255, 255, 255)
                self.cell(col_w, row_h, str(val).capitalize(), border=1, fill=fill, align="C")
            self.ln()

        self.ln(4)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*COLOR_SUBTEXT)
        self.cell(0, 5, "* Your Business column is highlighted. Values: Yes / No / Partial / Unknown")
        self.set_text_color(*COLOR_TEXT)

    def add_pricing_landscape(self, pricing: dict):
        self.add_page()
        self.section_title("Pricing Landscape")

        self.set_fill_color(*COLOR_SHADED)
        self.set_font("Helvetica", "", 10)
        self.set_x(20)
        self.multi_cell(
            170, 6,
            f"Market Low: {pricing.get('market_low', 'N/A')}   |   "
            f"Market High: {pricing.get('market_high', 'N/A')}   |   "
            f"Typical Range: {pricing.get('typical_range', 'N/A')}",
            fill=True,
        )
        self.ln(4)

        self.section_title("Positioning Recommendation", level=3)
        self.set_fill_color(220, 230, 250)
        self.set_font("Helvetica", "B", 10)
        self.set_x(20)
        self.multi_cell(170, 6, pricing.get("user_positioning_recommendation", ""), fill=True)
        self.ln(2)

        notes = pricing.get("notes", "")
        if notes:
            self.body_text(notes)

    def add_gaps_opportunities(self, gaps: list):
        self.add_page()
        self.section_title("Gaps & Opportunities")

        for i, item in enumerate(gaps, 1):
            self.ln(2)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*COLOR_PRIMARY)
            priority = item.get("priority", "medium")
            self.cell(8, 6, f"{i}.")
            self.priority_label(priority)
            self.ln(6)
            self.set_text_color(*COLOR_TEXT)

            self.set_font("Helvetica", "B", 10)
            self.set_x(25)
            self.cell(0, 5.5, "Gap:")
            self.ln(5.5)
            self.body_text(item.get("gap", ""), indent=10)

            self.set_font("Helvetica", "B", 10)
            self.set_x(25)
            self.cell(0, 5.5, "Opportunity:")
            self.ln(5.5)
            self.body_text(item.get("opportunity", ""), indent=10)
            self.ln(2)

    def add_recommendations(self, recommendations: list):
        self.add_page()
        self.section_title("Strategic Recommendations")

        for i, rec in enumerate(recommendations, 1):
            self.ln(3)
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(*COLOR_PRIMARY)
            priority = rec.get("priority", "medium")
            self.cell(8, 6, f"{i}.")
            self.priority_label(priority)
            self.ln(6)
            self.set_text_color(*COLOR_TEXT)

            self.set_font("Helvetica", "B", 10)
            self.body_text(rec.get("recommendation", ""))

            self.set_font("Helvetica", "I", 10)
            self.set_text_color(*COLOR_SUBTEXT)
            self.body_text(f"Rationale: {rec.get('rationale', '')}", indent=5)
            self.set_text_color(*COLOR_TEXT)

            actions = rec.get("action_items", [])
            if actions:
                self.set_font("Helvetica", "B", 9)
                self.body_text("Action Items:", indent=5)
                for action in actions:
                    self.bullet(action, indent=10)
            self.ln(2)

    def add_appendix(self, notes: str):
        self.add_page()
        self.section_title("Appendix: Data Quality Notes")
        self.body_text(notes or "All competitor data was collected and extracted successfully.")


def generate_pdf(
    analysis_path: str = ANALYSIS_PATH,
    business_info_path: str = BUSINESS_INFO_PATH,
    output_dir: str = OUTPUT_DIR,
) -> str:
    with open(analysis_path, encoding="utf-8") as f:
        analysis = json.load(f)
    with open(business_info_path, encoding="utf-8") as f:
        business_info = json.load(f)

    company = business_info.get("company_name", "Your Business")
    report = CompetitorReport(business_name=company)

    report.add_cover_page(business_info)
    report.add_executive_summary(analysis.get("executive_summary", ""))
    report.add_business_overview(business_info)

    for i, profile in enumerate(analysis.get("competitor_profiles", [])):
        report.add_competitor_profile(profile, i)

    if analysis.get("feature_matrix"):
        report.add_feature_matrix(analysis["feature_matrix"])

    if analysis.get("pricing_landscape"):
        report.add_pricing_landscape(analysis["pricing_landscape"])

    if analysis.get("gaps_and_opportunities"):
        report.add_gaps_opportunities(analysis["gaps_and_opportunities"])

    if analysis.get("strategic_recommendations"):
        report.add_recommendations(analysis["strategic_recommendations"])

    report.add_appendix(analysis.get("data_quality_notes", ""))

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"competitor_analysis_{timestamp}.pdf")
    report.output(output_path)

    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    path = generate_pdf()
    print(f"Done: {path}")
