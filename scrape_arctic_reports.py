import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import csv


url = "https://www.ncpor.res.in/arctics/display/452-reports"

response = requests.get(url)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

print("Page title:", soup.title.text.strip())


# -----------------------------------
# Find report download links
# -----------------------------------

reports = []

for link in soup.find_all("a"):

    text = link.get_text(" ", strip=True)

    href = link.get("href")

    if not href:
        continue

    # Look for DOWNLOAD links
    if text.upper() == "DOWNLOAD":

        download_url = urljoin(url, href)

        # -----------------------------------
        # Extract year from PDF filename
        # -----------------------------------

        year_match = re.search(
            r"(\d{4}-\d{2})",
            download_url
        )

        if year_match:
            year = year_match.group(1)
        else:
            year = ""


        # -----------------------------------
        # Extract expedition number
        # -----------------------------------
        # Current page = 15th expedition
        # We will improve this later for older
        # expedition reports.
        # -----------------------------------

        expedition_number = "15th"


        # -----------------------------------
        # Create report title
        # -----------------------------------

        title = "15th Indian Arctic Expedition Report"


        reports.append({

            "expedition_number": expedition_number,

            "title": title,

            "year": year,

            "report_type": "Expedition Report",

            "download_url": download_url,

            "source_url": url

        })


# -----------------------------------
# Display reports
# -----------------------------------

print("\n==============================")

print("TOTAL REPORTS:", len(reports))

print("==============================")


for i, report in enumerate(reports, start=1):

    print(f"\nReport {i}")

    print("Expedition:", report["expedition_number"])

    print("Title:", report["title"])

    print("Year:", report["year"])

    print("Type:", report["report_type"])

    print("Download URL:", report["download_url"])

    print("Source URL:", report["source_url"])