#!/usr/bin/env python3
"""
ecourts_causelist_scraper
- Downloads district court cause lists from eCourts and saves as PDF + JSON metadata.
- CLI: --district (required), --today / --tomorrow flags.
Notes:
- This is a simple HTML scraper converted to text-PDF using fpdf.
- Some districts/pages may require adjustments to selectors or session handling.
"""

import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import datetime
import os
import json
import click
import sys

BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/"

def ensure_output_dir():
    os.makedirs("output", exist_ok=True)

def fetch_cause_list_html(district):
    """
    Fetch cause list HTML for a district.
    NOTE: The actual eCourts site may require state/dist codes or different query params.
    If this simple GET doesn't work for a district, you'll need to inspect the form on the site
    and adapt params (or use Selenium for dynamic requests).
    """
    url = f"{BASE_URL}causelist/cause_list.php"
    # simple attempt: pass a district name as dist_code param if the site accepts it
    params = {"dist_code": district.lower()}
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"❌ Error while fetching cause list page: {e}")
        return None

def parse_cause_list_text(html, district, formatted_date):
    soup = BeautifulSoup(html, "html.parser")
    # Title fallback
    title_tag = soup.find("h4")
    title = title_tag.text.strip() if title_tag else "Cause List"
    # collect textual representation of tables (if any)
    tables = soup.find_all("table")
    content_lines = [title, "", f"District: {district.capitalize()}", f"Date: {formatted_date}", ""]
    if not tables:
        # no tables found: save the page text as fallback
        page_text = soup.get_text(separator="\n").strip()
        content_lines.append(page_text)
        return content_lines

    for idx, table in enumerate(tables, start=1):
        # optional: include small header for each table
        content_lines.append(f"--- Table {idx} ---")
        for row in table.find_all("tr"):
            cells = [c.text.strip() for c in row.find_all(["th", "td"])]
            # join with " | " for readability in PDF
            if cells:
                content_lines.append(" | ".join([c for c in cells if c]))
        content_lines.append("")  # blank line between tables
    return content_lines

def save_text_as_pdf(lines, pdf_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    for line in lines:
        # ensure lines are strings
        ln = str(line)
        # multi_cell wraps long lines
        pdf.multi_cell(0, 6, ln)
    pdf.output(pdf_path)

@click.command()
@click.option("--district", required=True, help="District name or code (e.g., nashik)")
@click.option("--today", is_flag=True, help="Download today's cause list")
@click.option("--tomorrow", is_flag=True, help="Download tomorrow's cause list")
def main(district, today, tomorrow):
    ensure_output_dir()

    if not (today or tomorrow):
        print("⚠️  Use --today or --tomorrow to specify date. Defaulting to today.")
    target_date = datetime.date.today() + datetime.timedelta(days=1 if tomorrow else 0)
    formatted_date = target_date.strftime("%d-%m-%Y")

    print(f"📅 Fetching cause list for {district.capitalize()} ({formatted_date}) ...")

    html = fetch_cause_list_html(district)
    if not html:
        print("❌ Failed to fetch cause list HTML. Exiting.")
        sys.exit(1)

    lines = parse_cause_list_text(html, district, formatted_date)

    # sanitize district name for filename
    safe_district = "".join([c if c.isalnum() or c in ("_", "-") else "_" for c in district.lower()])
    pdf_path = os.path.join("output", f"cause_list_{safe_district}_{formatted_date}.pdf")
    json_path = os.path.join("output", f"cause_list_{safe_district}_{formatted_date}.json")

    try:
        save_text_as_pdf(lines, pdf_path)
        meta = {
            "district": district,
            "date": formatted_date,
            "pdf_path": pdf_path,
            "lines_count": len(lines)
        }
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(meta, jf, indent=2, ensure_ascii=False)

        print(f"✅ Saved PDF: {pdf_path}")
        print(f"💾 Saved metadata: {json_path}")
    except Exception as e:
        print(f"💥 Error saving outputs: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
