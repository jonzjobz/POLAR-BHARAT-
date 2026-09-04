import requests
from bs4 import BeautifulSoup
import re
import csv


url = "https://www.ncpor.res.in/arctics/display/390-publications"

response = requests.get(url)

print("Status code:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

print("Page title:", soup.title.text.strip())


# -----------------------------------
# Find the publication table
# -----------------------------------

table = soup.find("table")

publications = []
current_year = None


# -----------------------------------
# Journal names used on the page
# -----------------------------------

journal_patterns = [
    "Journal of Basic Microbiology",
    "Indian J.Sci.Res",
    "Environmental Monitoring and Assessment",
    "Polar Science",
    "Catalysis Letters",
    "Current Science",
    "Marine Pollution Bulletin",
    "Data in Brief",
    "CZECH POLAR REPORTS",
    "PLos",
    "Geoscience Frontiers",
    "Annals of Microbiology",
    "Brazilian Journal of Microbiology",
    "3 Biotech",
    "Genome Announc",
    "International Journal of Marine Science",
    "Canadian Journal of Microbiology",
    "Atmospheric Research",
    "Cryobiology",
    "Extremophiles",
    "Polar Biology",
    "Polar Biol",
    "Polar Res",
    "Polar Rec",
    "Curr Microbiol",
    "Advances in Microbiology",
    "J Earth Syst Sci",
    "Adv Biosci Biotechnol",
    "Curr Sci",
    "Quat Int",
    "Scientificreports",
    "Tellus",
    "FEMS Microbiology",
    "Mausam",
    "Res Microbiol",
    "Indian J Mar Sci",
    "FEMS Microbiol",
]


# -----------------------------------
# Process every table row
# -----------------------------------

for row in table.find_all("tr"):

    text = row.get_text(" ", strip=True)

    if not text:
        continue


    # -----------------------------------
    # Check whether row is a year heading
    # -----------------------------------

    if re.fullmatch(r"(?:19|20)\d{2}", text):

        current_year = text

        continue


    if current_year is None:
        continue


    # -----------------------------------
    # Extract authors + publication year
    # -----------------------------------
    # IMPORTANT:
    # Use (?:19|20)\d{2} so the COMPLETE
    # year is captured.
    # -----------------------------------

    match = re.match(
        r"^(.*?)\s*\((?:(19|20)\d{2})\)\.\s*(.*)$",
        text
    )

    if match:

        authors = match.group(1).strip()

        # FIX:
        # Construct the complete year
        publication_year = match.group(2)

        # The above regex still separates 19/20,
        # so use a second extraction for the full year.
        year_match = re.search(r"\((19|20)\d{2}\)", text)

        if year_match:
            publication_year = year_match.group(0).strip("()")
        else:
            publication_year = current_year

        remaining = match.group(3).strip()

    else:

        authors = "Unknown"

        publication_year = current_year

        remaining = text


    # -----------------------------------
    # Find DOI
    # -----------------------------------

    doi = ""

    doi_match = re.search(
        r"(?:https?://(?:dx\.)?doi\.org/|doi:\s*)?"
        r"(10\.\d{4,9}/[-._;()/:\w]+)",
        text,
        re.IGNORECASE
    )

    if doi_match:

        doi = doi_match.group(1).rstrip(".,;)")

        # Remove DOI from remaining text
        remaining = re.sub(
            r"\(?\s*(?:https?://(?:dx\.)?doi\.org/|doi:\s*)?"
            r"10\.\d{4,9}/[-._;()/:\w]+\s*\)?",
            "",
            remaining,
            flags=re.IGNORECASE
        ).strip()


    # -----------------------------------
    # Separate title from journal
    # -----------------------------------

    title = remaining

    journal = ""

    journal_position = None

    for pattern in journal_patterns:

        position = remaining.lower().find(pattern.lower())

        if position != -1:

            if (
                journal_position is None
                or position < journal_position
            ):

                journal_position = position


    if journal_position is not None:

        title = remaining[:journal_position].strip()

        journal = remaining[journal_position:].strip()


    # -----------------------------------
    # Initialize publication details
    # -----------------------------------

    volume = ""
    issue = ""
    pages = ""


    # ===================================
    # FORMAT 1
    # Volume(Issue): Pages
    #
    # Examples:
    # 58(4):286-295
    # 20(1):56-62
    # 8 (1): 1-23
    # 115 (9):1690-1694
    # ===================================

    match = re.search(
        r"\b(\d+)\s*\(\s*(\d+)\s*\)\s*:\s*"
        r"(\d+(?:\s*[–-]\s*\d+)?)",
        journal
    )

    if match:

        volume = match.group(1)

        issue = match.group(2)

        pages = match.group(3).replace(" ", "")

        journal = journal[:match.start()].strip()


    # ===================================
    # FORMAT 2
    # Volume (Part A): Pages
    #
    # Example:
    # 131 (Part A): 453-459
    # ===================================

    else:

        match = re.search(
            r"\b(\d+)\s*\(\s*(Part\s+[^)]+)\s*\)\s*:\s*"
            r"(\d+(?:\s*[–-]\s*\d+)?)",
            journal,
            re.IGNORECASE
        )

        if match:

            volume = match.group(1)

            issue = match.group(2).strip()

            pages = match.group(3).replace(" ", "")

            journal = journal[:match.start()].strip()


    # ===================================
    # FORMAT 3
    # Volume: Pages
    #
    # Examples:
    # 190:22
    # 16:10-22
    # 148:712–724
    # 21:2522-2525
    # ===================================

    if not volume:

        match = re.search(
            r"\b(\d+)\s*:\s*"
            r"(\d+(?:\s*[–-]\s*\d+)?)",
            journal
        )

        if match:

            volume = match.group(1)

            pages = match.group(2).replace(" ", "")

            journal = journal[:match.start()].strip()


    # ===================================
    # FORMAT 4
    # Volume, Issue, pp Pages
    #
    # Example:
    # Volume 67, Issue 2, pp 203–214
    # ===================================

    if not volume:

        match = re.search(
            r"Volume\s+(\d+)"
            r"(?:\s*,?\s*Issue\s+(\d+))?"
            r"\s*,?\s*pp\.?\s*"
            r"(\d+(?:\s*[–-]\s*\d+)?)",
            journal,
            re.IGNORECASE
        )

        if match:

            volume = match.group(1)

            if match.group(2):

                issue = match.group(2)

            pages = match.group(3).replace(" ", "")

            journal = journal[:match.start()].strip()


    # ===================================
    # FORMAT 5
    # Volume + Pages without colon
    #
    # Example:
    # Some Journal 148:712–724
    #
    # This is mostly covered above.
    # ===================================


    # ===================================
    # FORMAT 6
    # Pages only
    #
    # Example:
    # Polar Science 10-22
    # ===================================

    if not pages:

        pages_match = re.search(
            r"(?:pp\.?\s*)?"
            r"(\d+(?:\s*[–-]\s*\d+)?)"
            r"\s*$",
            journal,
            re.IGNORECASE
        )

        if pages_match:

            pages = pages_match.group(1).replace(" ", "")

            journal = journal[:pages_match.start()].strip()


    # -----------------------------------
    # Special cleanup
    # -----------------------------------

    journal = journal.strip(" .,;:")


    # Remove accidental spaces
    journal = re.sub(r"\s+", " ", journal).strip()


    # -----------------------------------
    # Create details field
    # -----------------------------------

    details_parts = []

    if volume:

        details_parts.append("Volume " + volume)

    if issue:

        details_parts.append("Issue " + issue)

    if pages:

        details_parts.append("Pages " + pages)

    details = ", ".join(details_parts)


    # -----------------------------------
    # Store publication
    # -----------------------------------

    publications.append({

        "website_year": current_year,

        "publication_year": publication_year,

        "authors": authors,

        "title": title,

        "journal": journal,

        "volume": volume,

        "issue": issue,

        "pages": pages,

        "doi": doi,

        "details": details,

        "source_url": url

    })


# -----------------------------------
# Remove accidental empty records
# -----------------------------------

publications = [

    p for p in publications

    if p["title"].strip()

]


# -----------------------------------
# Display results
# -----------------------------------

print("\n==============================")

print("TOTAL PUBLICATIONS:", len(publications))

print("==============================")


for i, publication in enumerate(publications[:10], start=1):

    print(f"\nPublication {i}")

    print("Website year:", publication["website_year"])

    print("Publication year:", publication["publication_year"])

    print("Authors:", publication["authors"])

    print("Title:", publication["title"])

    print("Journal:", publication["journal"])

    print("Volume:", publication["volume"])

    print("Issue:", publication["issue"])

    print("Pages:", publication["pages"])

    print("DOI:", publication["doi"])

    print("Details:", publication["details"])


# -----------------------------------
# Save CSV
# -----------------------------------

filename = "polar_publications.csv"

with open(
    filename,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    fieldnames = [

        "website_year",

        "publication_year",

        "authors",

        "title",

        "journal",

        "volume",

        "issue",

        "pages",

        "doi",

        "details",

        "source_url"

    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(publications)


print("\nCSV file created:", filename)