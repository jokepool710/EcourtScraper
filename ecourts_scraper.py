"""
eCourts Cause List Scraper
Author: Tanishq Mahajan (J0KEP00L)
Date: October 2025
Description:
Fetches and downloads district court cause lists from https://services.ecourts.gov.in/
and optionally stores them as PDFs or JSON for analysis.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import argparse
from datetime import datetime, timedelta

# --- Constants ---
BASE_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/index/"
CAUSE_LIST_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=caselist/index/"

# --- Functions ---
def fetch_cause_list(district: str, day: str = "today"):
    """
    Fetches the cause list page for a given district and date (today/tomorrow).
    """
    date = datetime.now().date() if day == "today" else datetime.now().date() + timedelta(days=1)
    print(f"🔍 Fetching cause list for {district.title()} ({day.upper()}) — {date}")

    params = {
        "state_code": "26",   # Maharashtra code example
        "dist_code": district.lower(),
        "date": date.strftime("%d-%m-%Y")
    }

    try:
        response = requests.get(CAUSE_LIST_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f" Error fetching cause list: {e}")
        return None


def parse_cause_list(html_content: str):
    """
    Extracts case info and court names from HTML.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    table = soup.find("table")

    if not table:
        print(" No table found — likely no cause list for today.")
        return []

    data = []
    rows = table.find_all("tr")[1:]  # skip header row
    for row in rows:
        cols = [col.text.strip() for col in row.find_all("td")]
        if len(cols) >= 3:
            data.append({
                "serial_number": cols[0],
                "case_number": cols[1],
                "court_name": cols[2],
            })
    return data


def save_to_json(data, filename):
    """
    Saves scraped cause list info to JSON file.
    """
    os.makedirs("sample_output", exist_ok=True)
    filepath = os.path.join("sample_output", filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print(f" Saved JSON output → {filepath}")


def download_cause_list_pdf(district, day="today"):
    """
    Downloads cause list PDF if available.
    """
    date = datetime.now().date() if day == "today" else datetime.now().date() + timedelta(days=1)
    pdf_url = f"https://services.ecourts.gov.in/ecourtindia_v6/?p=caselist/download/{district}/{date.strftime('%d-%m-%Y')}"
    filename = f"sample_output/cause_list_{district}_{date}.pdf"

    try:
        response = requests.get(pdf_url, timeout=20)
        if "PDF" not in response.headers.get("Content-Type", ""):
            print(" No PDF available for this date.")
            return
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"📥 Cause list PDF saved → {filename}")
    except Exception as e:
        print(f" Failed to download PDF: {e}")


# --- CLI Handling ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="eCourts Cause List Scraper")
    parser.add_argument("--district", type=str, required=True, help="District name (e.g., nashik, pune)")
    parser.add_argument("--today", action="store_true", help="Fetch today's cause list")
    parser.add_argument("--tomorrow", action="store_true", help="Fetch tomorrow's cause list")
    parser.add_argument("--pdf", action="store_true", help="Download PDF version if available")

    args = parser.parse_args()
    day = "tomorrow" if args.tomorrow else "today"

    html = fetch_cause_list(args.district, day)
    if html:
        parsed = parse_cause_list(html)
        if parsed:
            filename = f"cause_list_info_{args.district}_{day}.json"
            save_to_json(parsed, filename)
        if args.pdf:
            download_cause_list_pdf(args.district, day)
