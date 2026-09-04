
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
START_URL = BASE_URL + "browse_by_keyword.action"

# For prototype
MAX_DATASETS_PER_CATEGORY = 10

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


# ==========================================
# STEP 1: GET MAIN CATEGORIES
# ==========================================

print("Getting main categories...")

response = session.get(START_URL)

print("STATUS:", response.status_code)

soup = BeautifulSoup(
    response.text,
    "html.parser"
)

categories = []

for link in soup.find_all("a"):

    text = link.get_text(" ", strip=True)
    href = link.get("href")

    if not text or not href:
        continue

    if (
        "entries" in text
        and
        "search_mf_topics_all.action" in href
    ):

        category = re.sub(
            r"\s*\(\d+\s*entries\)",
            "",
            text
        ).strip()

        full_url = urljoin(
            response.url,
            href
        )

        if category not in [
            x[0] for x in categories
        ]:

            categories.append(
                (
                    category,
                    full_url
                )
            )


print(
    "\nMAIN CATEGORIES FOUND:",
    len(categories)
)

for category, url in categories:

    print("-", category)


# ==========================================
# STEP 2: GET SUBCATEGORIES
# ==========================================

all_subcategories = []

print("\n\nGetting subcategories...")


for category, category_url in categories:

    print("\nCATEGORY:", category)

    response = session.get(category_url)

    if response.status_code != 200:

        print("Could not open category")

        continue

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    seen_urls = set()

    for link in soup.find_all("a"):

        text = link.get_text(
            " ",
            strip=True
        )

        href = link.get("href")

        if not text or not href:
            continue

        if "search_mf_title_all.action" not in href:
            continue

        # Ignore numbers such as 7, 16, 9
        if text.isdigit():
            continue

        full_url = urljoin(
            response.url,
            href
        )

        if full_url in seen_urls:
            continue

        seen_urls.add(full_url)

        all_subcategories.append(
            (
                category,
                text,
                full_url
            )
        )

        print("   ->", text)

    time.sleep(0.2)


print(
    "\nTOTAL SUBCATEGORIES:",
    len(all_subcategories)
)


# ==========================================
# STEP 3: GET MAX 10 DATASETS PER CATEGORY
# ==========================================

metadata_links = []

print("\n\nFinding prototype datasets...")


# Keep track of how many datasets
# we already found for each category

category_counts = {}


for category, subcategory, subcategory_url in all_subcategories:

    # Stop checking subcategories once
    # this category already has 10 datasets

    if category_counts.get(
        category,
        0
    ) >= MAX_DATASETS_PER_CATEGORY:

        continue


    print(
        "\n",
        category,
        ">",
        subcategory
    )


    response = session.get(
        subcategory_url
    )


    if response.status_code != 200:

        print(
            "FAILED:",
            response.status_code
        )

        continue


    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    for link in soup.find_all("a"):

        text = link.get_text(
            " ",
            strip=True
        )

        href = link.get("href")


        if not text or not href:
            continue


        # REAL DATASET LINK

        if text.lower() != "view metadata":
            continue


        if "search_mf_data.action" not in href:
            continue


        full_url = urljoin(
            response.url,
            href
        )


        # Avoid duplicate dataset URLs

        if any(
            x["url"] == full_url
            for x in metadata_links
        ):

            continue


        metadata_links.append(
            {
                "category": category,
                "subcategory": subcategory,
                "url": full_url
            }
        )


        category_counts[category] = (
            category_counts.get(
                category,
                0
            ) + 1
        )


        print(
            "   DATASET",
            category_counts[category]
        )


        # Stop at 10 for this category

        if (
            category_counts[category]
            >= MAX_DATASETS_PER_CATEGORY
        ):

            break


    time.sleep(0.2)


# ==========================================
# SHOW CATEGORY COUNTS
# ==========================================

print(
    "\n\n===================================="
)

print(
    "PROTOTYPE DATASET COUNTS"
)

print(
    "===================================="
)


for category, _ in categories:

    print(
        category,
        ":",
        category_counts.get(
            category,
            0
        )
    )


print(
    "\nTOTAL DATASETS TO SCRAPE:",
    len(metadata_links)
)

print(
    "===================================="
)


# ==========================================
# STEP 4: SCRAPE METADATA
# ==========================================

dataset_rows = []

print(
    "\n\nSCRAPING DATASET METADATA..."
)


for index, item in enumerate(
    metadata_links,
    start=1
):

    category = item["category"]

    subcategory = item["subcategory"]

    metadata_url = item["url"]


    print(
        f"\n[{index}/{len(metadata_links)}]",
        category,
        ">",
        subcategory
    )


    try:

        response = session.get(
            metadata_url,
            timeout=30
        )


        if response.status_code != 200:

            print(
                "FAILED:",
                response.status_code
            )

            continue


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # ==================================
        # GET PAGE TEXT
        # ==================================

        page_text = soup.get_text(
            "\n",
            strip=True
        )


        # ==================================
        # GET DATASET TITLE
        # ==================================

        dataset_title = ""


        # ----------------------------------
        # METHOD 1: Look for heading tags
        # ----------------------------------

        for tag in soup.find_all(
            ["h1", "h2", "h3", "h4"]
        ):

            heading = tag.get_text(
                " ",
                strip=True
            )

            if (
                heading
                and
                len(heading) > 5
                and
                "META DATA SEARCH" not in heading.upper()
            ):

                dataset_title = heading

                break


        # ----------------------------------
        # METHOD 2: Look for title labels
        # ----------------------------------

        if not dataset_title:

            for tag in soup.find_all(
                ["td", "th", "label", "div", "span"]
            ):

                text = tag.get_text(
                    " ",
                    strip=True
                )

                if text.lower() in [
                    "title",
                    "dataset title",
                    "data set title"
                ]:

                    next_text = tag.find_next()

                    if next_text:

                        value = next_text.get_text(
                            " ",
                            strip=True
                        )

                        if (
                            value
                            and
                            value.lower() != text.lower()
                        ):

                            dataset_title = value

                            break


        # ----------------------------------
        # METHOD 3: Search page text
        # ----------------------------------

        if not dataset_title:

            title_match = re.search(
                r"(?:Dataset Title|Data Set Title|Title)\s*[:\-]\s*(.+)",
                page_text,
                re.IGNORECASE
            )

            if title_match:

                dataset_title = (
                    title_match.group(1)
                    .strip()
                )


        # ----------------------------------
        # METHOD 4: Use page <title>
        # ----------------------------------

        if not dataset_title and soup.title:

            page_title = soup.title.get_text(
                " ",
                strip=True
            )

            if (
                page_title
                and
                "META DATA SEARCH" not in page_title.upper()
            ):

                dataset_title = page_title


        # ----------------------------------
        # Final fallback
        # ----------------------------------

        if not dataset_title:

            dataset_title = (
                category
                + " - "
                + subcategory
                + " Dataset"
            )


        # ==================================
        # SAVE DATA
        # ==================================

        dataset_rows.append(
            {
                "category": category,
                "subcategory": subcategory,
                "dataset_title": dataset_title,
                "metadata_url": metadata_url,
                "metadata_text": page_text
            }
        )


        print(
            "TITLE:",
            dataset_title
        )

        print(
            "SUCCESS"
        )


    except Exception as e:

        print(
            "ERROR:",
            e
        )


    time.sleep(0.15)


# ==========================================
# STEP 5: SAVE CSV
# ==========================================

filename = "npdc_prototype.csv"


with open(
    filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "category",
            "subcategory",
            "dataset_title",
            "metadata_url",
            "metadata_text"
        ]
    )

    writer.writeheader()

    writer.writerows(
        dataset_rows
    )


# ==========================================
# FINAL RESULT
# ==========================================

print(
    "\n\n===================================="
)

print(
    "PROTOTYPE SCRAPING COMPLETE"
)

print(
    "===================================="
)

print(
    "TOTAL DATASETS SCRAPED:",
    len(dataset_rows)
)

print(
    "CSV CREATED:",
    filename
)

print(
    "===================================="
)


# ==========================================
# PREVIEW
# ==========================================

print(
    "\nFIRST 5 DATASETS:\n"
)


for row in dataset_rows[:5]:

    print(
        row["category"],
        "|",
        row["subcategory"]
    )

    print(
        "TITLE:",
        row["dataset_title"]
    )

    print(
        "URL:",
        row["metadata_url"]
    )

    print()

