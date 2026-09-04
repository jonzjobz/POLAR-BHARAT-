
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import re
import time


# ==========================================
# SETTINGS
# ==========================================

BASE_URL = "https://npdc.ncpor.res.in/npdc/"

LOCATION_PAGE = (
    BASE_URL +
    "browse_by_location.action"
)

STATIONS = {
    "Maitri": "Antarctic",
    "Himadri": "Arctic",
    "Bharati": "Antarctic",
    "Dakshin Gangotri": "Antarctic"
}

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# ==========================================
# CLEAN TEXT
# ==========================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ==========================================
# GET STATION SEARCH LINKS
# ==========================================

print()
print("=" * 50)
print("     READING NPDC LOCATION PAGE")
print("=" * 50)

response = session.get(
    LOCATION_PAGE,
    timeout=30
)

print(
    "STATUS:",
    response.status_code
)

if response.status_code != 200:

    print(
        "Could not open location page."
    )

    exit()


soup = BeautifulSoup(
    response.text,
    "html.parser"
)


# ==========================================
# FIND STATION LINKS
# ==========================================

station_links = {}

for station in STATIONS:

    station_links[station] = None

    for link in soup.find_all("a"):

        text = clean_text(
            link.get_text(
                " ",
                strip=True
            )
        )

        href = link.get("href")

        if not href:
            continue

        # Exact station name
        if text.lower() != "click to view":
            continue

        if "search_mf_title.action" not in href:
            continue

        # Check station parameter
        if (
            "parameter=" +
            station.replace(" ", "+")
        ).lower() in href.lower():

            station_links[station] = urljoin(
                response.url,
                href
            )

            break


# ==========================================
# PRINT FOUND LINKS
# ==========================================

print()
print(
    "STATION SEARCH LINKS"
)

print()

for station, url in station_links.items():

    print(
        station,
        ":",
        url
    )


# ==========================================
# SCRAPE DATASETS
# ==========================================

all_rows = []


for station, expedition_type in STATIONS.items():

    search_url = station_links.get(
        station
    )

    print()
    print("=" * 50)
    print(
        "STATION:",
        station
    )
    print(
        "EXPEDITION TYPE:",
        expedition_type
    )
    print("=" * 50)

    if not search_url:

        print(
            "NO SEARCH LINK FOUND"
        )

        continue


    print(
        "SEARCH URL:",
        search_url
    )


    try:

        response = session.get(
            search_url,
            timeout=30
        )

    except Exception as e:

        print(
            "ERROR:",
            e
        )

        continue


    print(
        "STATUS:",
        response.status_code
    )


    if response.status_code != 200:

        print(
            "FAILED"
        )

        continue


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    # ======================================
    # FIND DATASET ROWS
    # ======================================

    dataset_links = []


    for link in soup.find_all("a"):

        text = clean_text(
            link.get_text(
                " ",
                strip=True
            )
        )

        href = link.get("href")


        if not href:
            continue


        # Actual metadata links
        if (
            "search_mf_data.action"
            not in href
        ):

            continue


        full_url = urljoin(
            response.url,
            href
        )


        # Avoid duplicate URLs
        if full_url in dataset_links:

            continue


        dataset_links.append(
            full_url
        )


    print(
        "DATASET LINKS FOUND:",
        len(dataset_links)
    )


    # ======================================
    # SCRAPE EACH DATASET
    # ======================================

    for index, dataset_url in enumerate(
        dataset_links,
        start=1
    ):

        print(
            f"[{index}/{len(dataset_links)}]",
            station
        )


        try:

            response = session.get(
                dataset_url,
                timeout=30
            )


            if response.status_code != 200:

                print(
                    "FAILED:",
                    response.status_code
                )

                continue


            dataset_soup = BeautifulSoup(
                response.text,
                "html.parser"
            )


            # --------------------------------
            # EXTRACT TITLE
            # --------------------------------

            title = ""


            # Find the label containing Title
            title_label = dataset_soup.find(
                "label",
                string=re.compile(
                    r"^\s*Title\s*$",
                    re.IGNORECASE
                )
            )


            if title_label:

                parent = title_label.parent

                if parent:

                    labels = parent.find_all(
                        "label"
                    )

                    for label in labels:

                        value = clean_text(
                            label.get_text(
                                " ",
                                strip=True
                            )
                        )

                        if (
                            value
                            and
                            value.lower()
                            != "title"
                        ):

                            title = value

                            break


            # --------------------------------
            # SECOND TITLE METHOD
            # --------------------------------

            if not title:

                page_title = dataset_soup.find(
                    "title"
                )

                if page_title:

                    candidate = clean_text(
                        page_title.get_text()
                    )

                    if (
                        candidate
                        and
                        candidate.upper()
                        != "META DATA SEARCH"
                    ):

                        title = candidate


            # --------------------------------
            # PAGE TEXT
            # --------------------------------

            metadata_text = clean_text(
                dataset_soup.get_text(
                    " ",
                    strip=True
                )
            )


            # --------------------------------
            # SAVE RECORD
            # --------------------------------

            all_rows.append({

                "station":
                    station,

                "expedition_type":
                    expedition_type,

                "source":
                    "NPDC",

                "title":
                    title,

                "metadata_url":
                    dataset_url,

                "metadata_text":
                    metadata_text

            })


            print(
                "TITLE:",
                title
                if title
                else "[TITLE NOT FOUND]"
            )


        except Exception as e:

            print(
                "ERROR:",
                e
            )


        time.sleep(0.1)


# ==========================================
# REMOVE DUPLICATES
# ==========================================

unique_rows = []

seen = set()


for row in all_rows:

    key = (
        row["station"],
        row["metadata_url"]
    )

    if key in seen:

        continue

    seen.add(key)

    unique_rows.append(
        row
    )


all_rows = unique_rows


# ==========================================
# SAVE CSV
# ==========================================

filename = (
    "npdc_station_datasets.csv"
)


with open(
    filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "station",
            "expedition_type",
            "source",
            "title",
            "metadata_url",
            "metadata_text"
        ]
    )

    writer.writeheader()

    writer.writerows(
        all_rows
    )


# ==========================================
# COUNTS
# ==========================================

counts = {}

for station in STATIONS:

    counts[station] = 0


for row in all_rows:

    counts[
        row["station"]
    ] += 1


# ==========================================
# FINAL OUTPUT
# ==========================================

print()
print("=" * 50)
print(
    "       NPDC STATION SCRAPING COMPLETE"
)
print("=" * 50)

print(
    "TOTAL DATASETS:",
    len(all_rows)
)

print(
    "CSV CREATED:",
    filename
)

print()
print(
    "=" * 50
)

print(
    "       STATION BREAKDOWN"
)

print(
    "=" * 50
)


for station in STATIONS:

    print(
        station,
        ":",
        counts[station],
        "datasets"
    )


# ==========================================
# PREVIEW
# ==========================================

print()
print(
    "=" * 50
)

print(
    "       FIRST 10 RECORDS"
)

print(
    "=" * 50
)


for row in all_rows[:10]:

    print()

    print(
        "Station:",
        row["station"]
    )

    print(
        "Title:",
        row["title"]
    )

    print(
        "URL:",
        row["metadata_url"]
    )


print()
print(
    "=" * 50
)

print(
    "DONE"
)

print(
    "=" * 50
)

