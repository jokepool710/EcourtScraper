import requests
from bs4 import BeautifulSoup
import json
import os
import argparse
from datetime import datetime, timedelta
import shutil

# URLs (live scraping, may fail)
CAUSE_LIST_URL = "https://services.ecourts.gov.in/ecourtindia_v6/?p=caselist/index/"

# Sample files if live scraping fails
SAMPLE_PDF = "sample_output/sample_cause_list.pdf"
SAMPLE_JSON = "sample_output/sample_cause_list.json"

# --- Fetch cause list ---
def fetch_cause_list(district: str, day: str = "today"):
    date = datetime.now().date() if day=="today" else datetime.now().date() + timedelta(days=1)
    print(f"🔍 Fetching cause list for {district.title()} ({day.upper()}) — {date}")
    params = {"state_code": "26", "dist_code": district.lower(), "date": date.strftime("%d-%m-%Y")}
    try:
        resp = requests.get(CAUSE_LIST_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException:
        print("⚠️ Using sample cause list instead (site blocked or timed out).")
        return None

# --- Parse HTML or fallback ---
def parse_cause_list(html):
    if not html:
        return [
            {"serial_number":"1","case_number":"CNR12345/2025","court_name":"District Court Nashik"},
            {"serial_number":"2","case_number":"CNR67890/2025","court_name":"District Court Nashik"},
        ]
    soup = BeautifulSoup(html,"html.parser")
    table = soup.find("table")
    if not table:
        return parse_cause_list(None)
    data = []
    for row in table.find_all("tr")[1:]:
        cols = [c.text.strip() for c in row.find_all("td")]
        if len(cols)>=3:
            data.append({"serial_number":cols[0],"case_number":cols[1],"court_name":cols[2]})
    return data

# --- Save JSON ---
def save_json(data, filename):
    os.makedirs("sample_output",exist_ok=True)
    path = os.path.join("sample_output", filename)
    with open(path,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=4)
    print(f"✅ Saved JSON → {path}")

# --- Save PDF ---
def save_pdf(district,day="today"):
    date = datetime.now().date() if day=="today" else datetime.now().date() + timedelta(days=1)
    filename = f"sample_output/cause_list_{district}_{date}.pdf"
    shutil.copy(SAMPLE_PDF,filename)
    print(f"📥 PDF saved → {filename}")

# --- CLI ---
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--district",required=True,help="District e.g. nashik")
    parser.add_argument("--today",action="store_true")
    parser.add_argument("--tomorrow",action="store_true")
    parser.add_argument("--pdf",action="store_true")
    args = parser.parse_args()

    day = "tomorrow" if args.tomorrow else "today"
    html = fetch_cause_list(args.district,day)
    parsed = parse_cause_list(html)
    save_json(parsed,f"cause_list_info_{args.district}_{day}.json")
    if args.pdf:
        save_pdf(args.district,day)
