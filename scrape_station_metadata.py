import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import re

# ==================================================
# SETTINGS
# ==================================================

INPUT_FILE = "npdc_station_datasets.csv"
OUTPUT_FILE = "npdc_station_metadata.csv"

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

# ==================================================
# LOAD CSV
# ==================================================

print("=" * 60)
print("       NPDC STATION METADATA SCRAPER")
print("=" * 60)

print("\nLoading station dataset file...")

df = pd.read_csv(INPUT_FILE)

print("Records loaded:", len(df))
print("Columns found:")

for column in df.columns:
    print("-", column)

# ==================================================
# FIND URL COLUMN AUTOMATICALLY
# ==================================================

url_column = None

possible_url_columns = [
    "url",
    "URL",
    "metadata_url",
    "Metadata URL",
    "link",
    "Link"
]

for column in possible_url_columns:

    if column in df.columns:
        url_column = column
        break

if url_column is None:

    print("\nERROR: Could not find URL column.")
    print("Available columns:", list(df.columns))
    print("\nPlease stop here.")
    exit()

print("\nUsing URL column:", url_column)

# ==================================================
# HELPER FUNCTION
# ==================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==================================================
# EXTRACT PAGE CONTENT
# ==================================================

def extract_page_content(soup):

    # ----------------------------------------------
    # PAGE TITLE
    # ----------------------------------------------

    page_title = ""

    if soup.title:

        page_title = clean_text(
            soup.title.get_text()
        )

    # ----------------------------------------------
    # PAGE TEXT
    # ----------------------------------------------

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    # ----------------------------------------------
    # FIND POSSIBLE DATASET TITLE
    # ----------------------------------------------

    dataset_title = ""

    headings = soup.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "strong",
            "b"
        ]
    )

    ignored_words = [
        "NPDC",
        "Home",
        "Metadata",
        "META DATA SEARCH",
        "Search",
        "Search Results",
        "Browse"
    ]

    for heading in headings:

        text = clean_text(
            heading.get_text()
        )

        if not text:
            continue

        if text in ignored_words:
            continue

        if len(text) > len(dataset_title):

            dataset_title = text

    return (
        page_title,
        dataset_title,
        page_text
    )


# ==================================================
# SCRAPE
# ==================================================

results = []

successful = 0
failed = 0
skipped = 0

print("\n")
print("=" * 60)
print("       STARTING METADATA SCRAPING")
print("=" * 60)

for index, row in df.iterrows():

    station = str(
        row.get("station", "")
    ).strip()

    title_from_csv = str(
        row.get("title", "")
    ).strip()

    url = str(
        row.get(url_column, "")
    ).strip()

    print(
        f"\n[{index + 1}/{len(df)}] {station}"
    )

    print(
        "URL:",
        url
    )

    # ==================================================
    # CHECK URL
    # ==================================================

    if (
        not url
        or url.lower() == "nan"
        or not url.startswith("http")
    ):

        print("SKIPPED: Invalid or missing URL")

        skipped += 1

        continue

    # ==================================================
    # REQUEST
    # ==================================================

    try:

        response = session.get(
            url,
            timeout=30
        )

        print(
            "STATUS:",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "FAILED HTTP STATUS:",
                response.status_code
            )

            failed += 1

            continue

        # ==================================================
        # PARSE
        # ==================================================

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        (
            page_title,
            detected_title,
            page_text
        ) = extract_page_content(soup)

        # ==================================================
        # CHOOSE BEST TITLE
        # ==================================================

        if (
            title_from_csv
            and title_from_csv.lower() != "nan"
            and title_from_csv.lower() != "meta data search"
        ):

            final_title = title_from_csv

        elif detected_title:

            final_title = detected_title

        else:

            final_title = page_title

        # ==================================================
        # SAVE
        # ==================================================

        results.append({

            "station": station,

            "polar_region":
                (
                    "Arctic"
                    if station.lower() == "himadri"
                    else "Antarctica"
                ),

            "source": "NPDC",

            "content_type":
                "Scientific Dataset",

            "title": final_title,

            "metadata_url": url,

            "page_title": page_title,

            "metadata_text": page_text

        })

        successful += 1

        print(
            "TITLE:",
            final_title
        )

        print(
            "PAGE TEXT LENGTH:",
            len(page_text)
        )

        print("SUCCESS")

    except Exception as e:

        failed += 1

        print(
            "ERROR:",
            e
        )

    # ==================================================
    # DELAY
    # ==================================================

    time.sleep(0.2)


# ==================================================
# CREATE DATAFRAME
# ==================================================

result_df = pd.DataFrame(
    results
)

# ==================================================
# REMOVE DUPLICATES
# ==================================================

if len(result_df) > 0:

    before = len(result_df)

    result_df = result_df.drop_duplicates(
        subset=["metadata_url"]
    )

    after = len(result_df)

    print(
        "\nDuplicate records removed:",
        before - after
    )

# ==================================================
# SAVE CSV
# ==================================================

result_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)

# ==================================================
# FINAL REPORT
# ==================================================

print("\n")
print("=" * 60)
print("       STATION METADATA SCRAPING COMPLETE")
print("=" * 60)

print(
    "TOTAL INPUT RECORDS:",
    len(df)
)

print(
    "SUCCESSFUL:",
    successful
)

print(
    "FAILED:",
    failed
)

print(
    "SKIPPED:",
    skipped
)

print(
    "TOTAL OUTPUT RECORDS:",
    len(result_df)
)

print(
    "CSV CREATED:",
    OUTPUT_FILE
)

# ==================================================
# STATION BREAKDOWN
# ==================================================

print("\n")
print("=" * 60)
print("       STATION BREAKDOWN")
print("=" * 60)

if len(result_df) > 0:

    counts = (
        result_df["station"]
        .value_counts()
    )

    for station, count in counts.items():

        print(
            station,
            ":",
            count,
            "records"
        )

# ==================================================
# PREVIEW
# ==================================================

print("\n")
print("=" * 60)
print("       FIRST 5 RECORDS")
print("=" * 60)

for _, row in result_df.head(5).iterrows():

    print("\nStation:", row["station"])

    print(
        "Title:",
        row["title"]
    )

    print(
        "URL:",
        row["metadata_url"]
    )

    print(
        "Metadata characters:",
        len(
            str(
                row["metadata_text"]
            )
        )
    )

print("\n")
print("=" * 60)
print("DONE")
print("=" * 60)