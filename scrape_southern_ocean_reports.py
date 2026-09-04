import requests
import csv


# -----------------------------------
# Southern Ocean report information
# -----------------------------------

reports = [

    {
        "year": "2012",
        "title": "Southern Ocean Expedition Report 2012",
        "report_type": "Cruise Report",
        "download_url": "http://www.ncpor.res.in/files/so_cruise_reports/SOE 2012.pdf"
    },

    {
        "year": "2011",
        "title": "Southern Ocean Expedition Report 2011",
        "report_type": "Cruise Report",
        "download_url": "http://www.ncpor.res.in/files/so_cruise_reports/SOE 2011.pdf"
    },

    {
        "year": "2010",
        "title": "Southern Ocean Expedition Report 2010",
        "report_type": "Cruise Report",
        "download_url": "http://www.ncpor.res.in/files/so_cruise_reports/SOE 2010.pdf"
    },

    {
        "year": "2009",
        "title": "Southern Ocean Expedition Report 2009",
        "report_type": "Cruise Report",
        "download_url": "http://www.ncpor.res.in/files/so_cruise_reports/SOE 2009.pdf"
    },

    {
        "year": "2006",
        "title": "Southern Ocean Expedition Report 2006",
        "report_type": "Cruise Report",
        "download_url": "http://www.ncpor.res.in/files/so_cruise_reports/SOE 2006.pdf"
    },

    {
        "year": "2004",
        "title": "Southern Ocean Expedition Report 2004",
        "report_type": "Cruise Report",
        "download_url": "http://www.ncpor.res.in/files/so_cruise_reports/SOE 2004.pdf"
    }

]


# -----------------------------------
# Source page
# -----------------------------------

source_url = "https://www.ncpor.res.in/pages/display/97-southernocean"


# Add source URL to every report
for report in reports:
    report["source_url"] = source_url


# -----------------------------------
# Display results
# -----------------------------------

print("\n==============================")
print("TOTAL SOUTHERN OCEAN REPORTS:", len(reports))
print("==============================")


for i, report in enumerate(reports, start=1):

    print(f"\nReport {i}")

    print("Year:", report["year"])
    print("Title:", report["title"])
    print("Type:", report["report_type"])
    print("Download URL:", report["download_url"])
    print("Source URL:", report["source_url"])


# -----------------------------------
# Save CSV
# -----------------------------------

filename = "polar_southern_ocean_reports.csv"


with open(
    filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    fieldnames = [
        "year",
        "title",
        "report_type",
        "download_url",
        "source_url"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(reports)


print("\nCSV file created:", filename)