import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import csv
import re


# ==========================================
# NCPOR ARCTIC PAGES
# ==========================================

pages = {

    "Arctic Home":
        "https://www.ncpor.res.in/arctics",

    "Himadri":
        "https://www.ncpor.res.in/arctics/display/394-himadri",

    "Field Activities":
        "https://www.ncpor.res.in/arctics/display/397-long-term-monitoring-",

    "IndARC":
        "https://www.ncpor.res.in/arctics/display/398-indarc",

    "Cryosphere":
        "https://www.ncpor.res.in/arctics/display/399-cryosphere",

    "Atmospheric Studies":
        "https://www.ncpor.res.in/arctics/display/400-atmospheric-studies"

}


# ==========================================
# STORAGE
# ==========================================

images = []

seen_urls = set()


# ==========================================
# IMAGE FILTER
# ==========================================

def is_useful_image(image_url):

    filename = image_url.lower().split("/")[-1]

    unwanted = [

        "normal.gif",
        "yellow.gif",
        "increase.gif",
        "decrease.gif",
        "logo.png",
        "right-logo.png"

    ]

    for item in unwanted:

        if item in filename:
            return False

    return True


# ==========================================
# SCRAPE EACH PAGE
# ==========================================

for page_name, url in pages.items():

    print("\n================================")
    print("PAGE:", page_name)
    print("================================")

    try:

        response = requests.get(
            url,
            timeout=15
        )

        print(
            "Status code:",
            response.status_code
        )

        if response.status_code != 200:

            print("Could not access page.")

            continue


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # ==================================
        # FIND IMAGES
        # ==================================

        page_image_count = 0


        for img in soup.find_all("img"):

            image_url = img.get(
                "src",
                ""
            ).strip()


            if not image_url:

                continue


            # ==============================
            # FULL URL
            # ==============================

            image_url = urljoin(
                url,
                image_url
            )


            # ==============================
            # FILTER
            # ==============================

            if not is_useful_image(
                image_url
            ):

                continue


            # ==============================
            # DUPLICATES
            # ==============================

            if image_url in seen_urls:

                continue


            seen_urls.add(
                image_url
            )


            # ==============================
            # TITLE
            # ==============================

            title = img.get(
                "alt",
                ""
            ).strip()


            if not title:

                title = page_name


            title = re.sub(
                r"\s+",
                " ",
                title
            ).strip()


            # ==============================
            # STORE
            # ==============================

            images.append({

                "title": title,

                "category": page_name,

                "image_url": image_url,

                "source_url": url

            })


            page_image_count += 1


        print(
            "Useful images found:",
            page_image_count
        )


    except Exception as e:

        print(
            "Error:",
            e
        )


# ==========================================
# TOTAL
# ==========================================

print("\n================================")
print(
    "TOTAL USEFUL IMAGES:",
    len(images)
)
print("================================")


# ==========================================
# DISPLAY
# ==========================================

for i, image in enumerate(
    images,
    start=1
):

    print(
        f"\nImage {i}"
    )

    print(
        "Title:",
        image["title"]
    )

    print(
        "Category:",
        image["category"]
    )

    print(
        "Image URL:",
        image["image_url"]
    )

    print(
        "Source:",
        image["source_url"]
    )


# ==========================================
# SAVE CSV
# ==========================================

filename = "polar_images.csv"


with open(
    filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    fieldnames = [

        "title",
        "category",
        "image_url",
        "source_url"

    ]


    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )


    writer.writeheader()

    writer.writerows(
        images
    )


print(
    "\nCSV file created:",
    filename
)