import requests
from bs4 import BeautifulSoup
import csv
import re
from urllib.parse import urljoin


# ==========================================
# URL
# ==========================================

url = "https://www.ncpor.res.in/arctics/display/392-team-members"

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


# ==========================================
# STORAGE
# ==========================================

team_members = []

current_department = ""


# ==========================================
# DEPARTMENT NAMES
# ==========================================

department_names = [
    "Arctic Operations",
    "Arctic Expedition Logistics",
    "Ocean Atmospheric Studies",
    "Arctic Ecology & Biogeochemistry"
]


# ==========================================
# FIND ALL ELEMENTS
# ==========================================

for element in content.find_all(
    ["h1", "h2", "h3", "h4", "strong", "li"]
):

    text = element.get_text(" ", strip=True)

    if not text:
        continue

    text = re.sub(r"\s+", " ", text).strip()


    # ======================================
    # CHECK FOR DEPARTMENT
    # ======================================

    matched_department = None

    for department in department_names:

        if department.lower() in text.lower():

            matched_department = department
            break


    if matched_department:

        current_department = matched_department

        print("\nDepartment:", current_department)

        continue


    # ======================================
    # FIND PERSON LINK
    # ======================================

    link = element.find(
        "a",
        href=re.compile(r"/profiles/details/")
    )

    if link is None:
        continue


    # ======================================
    # GET NAME
    # ======================================

    name = link.get_text(" ", strip=True)

    name = re.sub(
        r"\s+",
        " ",
        name
    ).strip()


    # ======================================
    # GET PROFILE URL
    # ======================================

    profile_url = link.get("href", "").strip()

    if not name or not profile_url:
        continue


    # ======================================
    # MAKE FULL URL
    # ======================================

    profile_url = urljoin(
        "https://www.ncpor.res.in",
        profile_url
    )


    # ======================================
    # EXTRACT DESIGNATION
    # ======================================

    designation = text

    # Remove person's name
    designation = re.sub(
        re.escape(name),
        "",
        designation,
        count=1,
        flags=re.IGNORECASE
    )

    # Remove leftover separators
    designation = designation.strip(
        " -–—:."
    )

    # Remove accidental repeated name
    designation = re.sub(
        re.escape(name),
        "",
        designation,
        flags=re.IGNORECASE
    )

    # Clean spaces
    designation = re.sub(
        r"\s+",
        " ",
        designation
    ).strip()


    # ======================================
    # STORE MEMBER
    # ======================================

    team_members.append({

        "department": current_department,

        "name": name,

        "designation": designation,

        "profile_url": profile_url,

        "source_url": url

    })


# ==========================================
# REMOVE DUPLICATES
# ==========================================

unique_members = []

seen = set()

for member in team_members:

    key = (
        member["name"],
        member["profile_url"],
        member["department"]
    )

    if key not in seen:

        seen.add(key)

        unique_members.append(member)


team_members = unique_members


# ==========================================
# DISPLAY RESULTS
# ==========================================

print("\n==============================")

print(
    "TOTAL TEAM MEMBERS:",
    len(team_members)
)

print("==============================")


for i, member in enumerate(
    team_members,
    start=1
):

    print(f"\nMember {i}")

    print(
        "Department:",
        member["department"]
    )

    print(
        "Name:",
        member["name"]
    )

    print(
        "Designation:",
        member["designation"]
    )

    print(
        "Profile URL:",
        member["profile_url"]
    )


# ==========================================
# SAVE CSV
# ==========================================

filename = "arctic_team_members.csv"

with open(
    filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    fieldnames = [
        "department",
        "name",
        "designation",
        "profile_url",
        "source_url"
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(team_members)


print(
    "\nCSV file created:",
    filename
)