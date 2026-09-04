import requests
from bs4 import BeautifulSoup
import csv
import re

# ==========================================
# URL
# ==========================================

url = "https://www.ncpor.res.in/arctics/display/391-projects-implemented"

response = requests.get(url)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

print("Page title:", soup.title.text.strip())


# ==========================================
# FIND MAIN CONTENT
# ==========================================

content = soup.find("div", id="leftColumn")

if content is None:
    content = soup

text = content.get_text("\n", strip=True)


# ==========================================
# PROJECT STORAGE
# ==========================================

projects = []

current_phase = ""
current_start_date = ""
current_end_date = ""


# ==========================================
# FIND TABLE
# ==========================================

table = content.find("table")

if table is None:
    print("ERROR: Project table not found.")
    exit()


# ==========================================
# PROCESS ROWS
# ==========================================

for row in table.find_all("tr"):

    cells = row.find_all(["td", "th"])

    cell_texts = [
        cell.get_text(" ", strip=True)
        for cell in cells
    ]

    cell_texts = [
        re.sub(r"\s+", " ", text).strip()
        for text in cell_texts
    ]

    # Remove completely empty cells
    cell_texts = [x for x in cell_texts if x]

    if not cell_texts:
        continue


    # ======================================
    # CHECK FOR PHASE HEADING
    # ======================================

    row_text = " ".join(cell_texts)

    phase_match = re.search(
        r"(SUMMER PHASE|WINTER PHASE)"
        r"\s*([IVX]*)"
        r"\s*:?\s*"
        r"(.+)?",
        row_text,
        re.IGNORECASE
    )

    if phase_match:

        current_phase = (
            phase_match.group(1).title()
            + " "
            + phase_match.group(2).upper()
        ).strip()

        date_text = phase_match.group(3) or ""

        # ----------------------------------
        # Extract dates
        # ----------------------------------

        date_match = re.search(
            r"(\d{1,2})[.\-/ ]+"
            r"(\d{1,2})[.\-/ ]+"
            r"(\d{4})"
            r"\s*(?:to|-)\s*"
            r"(\d{1,2})[.\-/ ]+"
            r"(\d{1,2})[.\-/ ]+"
            r"(\d{4})",
            date_text
        )

        if date_match:

            current_start_date = (
                f"{date_match.group(1)}-"
                f"{date_match.group(2)}-"
                f"{date_match.group(3)}"
            )

            current_end_date = (
                f"{date_match.group(4)}-"
                f"{date_match.group(5)}-"
                f"{date_match.group(6)}"
            )

        else:

            # Try date format such as:
            # 08.10.2018 to 05.11.2018
            date_match = re.search(
                r"(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})"
                r"\s*(?:to|-)\s*"
                r"(\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})",
                date_text
            )

            if date_match:

                current_start_date = date_match.group(1)
                current_end_date = date_match.group(2)

        continue


    # ======================================
    # NORMAL PROJECT ROW
    # ======================================

    # We need at least 3 columns:
    # SI No | Project Name | Organization

    if len(cell_texts) >= 3:

        # First column = serial number
        serial = cell_texts[0]

        # Check if first cell looks like a number
        if re.fullmatch(r"\d+\.?", serial):

            project_name = cell_texts[1]

            organization = " ".join(cell_texts[2:])

            # Avoid accidentally storing headers
            if (
                project_name.lower() == "project name"
                or organization.lower() == "participating organization"
            ):
                continue

            projects.append({

                "phase": current_phase,

                "start_date": current_start_date,

                "end_date": current_end_date,

                "project": project_name,

                "organization": organization,

                "source_url": url

            })


# ==========================================
# REMOVE EMPTY / BAD RECORDS
# ==========================================

projects = [
    p for p in projects
    if p["project"].strip()
]


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n==============================")
print("TOTAL PROJECTS:", len(projects))
print("==============================")


for i, project in enumerate(projects[:20], start=1):

    print(f"\nProject {i}")

    print("Phase:", project["phase"])

    print("Start Date:", project["start_date"])

    print("End Date:", project["end_date"])

    print("Project:", project["project"])

    print("Organization:", project["organization"])


# ==========================================
# SAVE CSV
# ==========================================

filename = "arctic_projects.csv"

with open(
    filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    fieldnames = [
        "phase",
        "start_date",
        "end_date",
        "project",
        "organization",
        "source_url"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(projects)


print("\nCSV file created:", filename)