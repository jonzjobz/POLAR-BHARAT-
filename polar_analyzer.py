
# polar_analyzer.py
# ============================================================
# POLAR RESEARCH ANALYSIS ENGINE
# Prototype Version
#
# PRIMARY DATA SOURCES:
#   arctic_projects.csv
#   arctic_team_members.csv
#   npdc_datasets.csv
#   npdc_prototype.csv
#   npdc_station_metadata.csv
#   polar_images.csv 
#   polar_publications.csv
#   polar_southern_ocean_reports.csv
#
# NOT USED:
#   polar_knowledge_base.csv
#   polar_station_data.csv
#   npdc_station_datasets.csv
#   station_summary.csv
#   create_station_csv.py
# ============================================================

import pandas as pd
import re
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

TOP_RESULTS = 10


PRIMARY_FILES = [
    "arctic_projects.csv",
    "arctic_team_members.csv",
    "npdc_datasets.csv",
    "npdc_prototype.csv",
    "npdc_station_metadata.csv",
    "polar_images.csv",
    "polar_publications.csv",
    "polar_southern_ocean_reports.csv"
]


# ============================================================
# LOAD PRIMARY DATA
# ============================================================

def load_primary_data():

    print("\n" + "=" * 70)
    print("          LOADING PRIMARY POLAR DATA")
    print("=" * 70)

    all_records = []

    for filename in PRIMARY_FILES:

        filepath = BASE_DIR / filename

        if not filepath.exists():

            print(f"\nWARNING: {filename} not found.")
            continue

        try:

            df = pd.read_csv(
                filepath,
                low_memory=False
            )

            print(
                f"{filename:<35} "
                f"{len(df):>5} records"
            )

            # ------------------------------------------------
            # Add source file
            # ------------------------------------------------

            df["source_file"] = filename

            # ------------------------------------------------
            # Standardize important columns
            # ------------------------------------------------

            if "source" not in df.columns:

                if filename.startswith("arctic_"):

                    df["source"] = "NCPOR"

                elif filename.startswith("npdc_"):

                    df["source"] = "NPDC"

                else:

                    df["source"] = "NCPOR"

            # ------------------------------------------------
            # Add content type if missing
            # ------------------------------------------------

            if "content_type" not in df.columns:

                if filename == "arctic_projects.csv":

                    df["content_type"] = "Arctic Project"

                elif filename == "arctic_team_members.csv":

                    df["content_type"] = "Team Member"

                elif filename == "npdc_datasets.csv":

                    df["content_type"] = "Scientific Dataset Index"

                elif filename == "npdc_prototype.csv":

                    df["content_type"] = "Scientific Dataset"

                elif filename == "npdc_station_metadata.csv":

                    df["content_type"] = "Station Dataset"

                elif filename == "polar_images.csv":

                    df["content_type"] = "Image"

                elif filename == "polar_publications.csv":

                    df["content_type"] = "Publication"

                elif filename == "polar_southern_ocean_reports.csv":

                    df["content_type"] = "Southern Ocean Report"

            all_records.append(df)

        except Exception as e:

            print(
                f"\nERROR loading {filename}: {e}"
            )

    if not all_records:

        print("\nERROR: No primary CSV files could be loaded.")

        return None

    combined = pd.concat(
        all_records,
        ignore_index=True,
        sort=False
    )

    print("\n" + "-" * 70)
    print(
        f"TOTAL RAW PRIMARY RECORDS: {len(combined)}"
    )

    return combined


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):

    if pd.isna(value):
        return ""

    text = str(value).lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# TITLE EXTRACTION
# ============================================================

def get_title(row):

    possible_columns = [
        "title",
        "dataset_title",
        "project",
        "name"
    ]

    for column in possible_columns:

        if column not in row.index:
            continue

        value = row[column]

        if pd.isna(value):
            continue

        value = str(value).strip()

        if value:
            return value

    return "Untitled record"


# ============================================================
# NORMALIZE TITLE
# ============================================================

def normalize_title(title):

    if pd.isna(title):
        return ""

    title = str(title).lower()

    # Fix common spacing problems
    title = re.sub(
        r"\s+",
        " ",
        title
    )

    # Remove punctuation
    title = re.sub(
        r"[^a-z0-9\s]",
        " ",
        title
    )

    title = re.sub(
        r"\s+",
        " ",
        title
    )

    return title.strip()


# ============================================================
# CREATE SEARCH TEXT
# ============================================================

def create_search_text(df):

    searchable_columns = [
        "title",
        "dataset_title",
        "project",
        "category",
        "subcategory",
        "authors",
        "journal",
        "details",
        "metadata_text",
        "report_type",
        "name",
        "department",
        "designation",
        "station",
        "polar_region"
    ]

    available_columns = [
        column
        for column in searchable_columns
        if column in df.columns
    ]

    df["search_text"] = ""

    for column in available_columns:

        df["search_text"] += (
            df[column]
            .fillna("")
            .astype(str)
            .str.lower()
            + " "
        )

    return df


# ============================================================
# KEYWORD EXTRACTION
# ============================================================

def extract_keywords(query):

    query = query.lower()

    query = re.sub(
        r"[^a-z0-9\s-]",
        " ",
        query
    )

    words = query.split()

    stopwords = {
        "the",
        "a",
        "an",
        "of",
        "and",
        "or",
        "in",
        "on",
        "for",
        "to",
        "is",
        "are",
        "about",
        "show",
        "me",
        "tell",
        "what",
        "does",
        "do",
        "how",
        "can",
        "research",
        "polar"
    }

    return [
        word
        for word in words
        if word not in stopwords
    ]


# ============================================================
# RELEVANCE SCORE
# ============================================================

def calculate_score(row, keywords):

    score = 0

    title = clean_text(
        row.get("title", "")
    )

    dataset_title = clean_text(
        row.get("dataset_title", "")
    )

    project = clean_text(
        row.get("project", "")
    )

    category = clean_text(
        row.get("category", "")
    )

    subcategory = clean_text(
        row.get("subcategory", "")
    )

    details = clean_text(
        row.get("details", "")
    )

    metadata = clean_text(
        row.get("metadata_text", "")
    )

    station = clean_text(
        row.get("station", "")
    )

    search_text = clean_text(
        row.get("search_text", "")
    )

    for keyword in keywords:

        # Strong title match
        if keyword in title:
            score += 10

        # Dataset title
        if keyword in dataset_title:
            score += 9

        # Project
        if keyword in project:
            score += 8

        # Category
        if keyword in category:
            score += 6

        # Subcategory
        if keyword in subcategory:
            score += 6

        # Station
        if keyword in station:
            score += 8

        # Details
        if keyword in details:
            score += 3

        # Metadata
        if keyword in metadata:
            score += 2

        # General occurrence
        if keyword in search_text:
            score += 1

    return score


# ============================================================
# REMOVE DUPLICATES
# ============================================================

def remove_duplicates(df):

    if len(df) == 0:
        return df

    df = df.copy()

    # --------------------------------------------------------
    # Create normalized title
    # --------------------------------------------------------

    df["normalized_title"] = df.apply(
        lambda row: normalize_title(
            get_title(row)
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Sort by relevance
    # --------------------------------------------------------

    df = df.sort_values(
        by="score",
        ascending=False
    )

    before = len(df)

    # --------------------------------------------------------
    # Remove duplicate titles
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=["normalized_title"],
        keep="first"
    )

    after = len(df)

    print(
        f"\nDuplicate research records removed: "
        f"{before - after}"
    )

    return df


# ============================================================
# STATION DETECTION
# ============================================================

STATIONS = {

    "Maitri": [
        "maitri"
    ],

    "Himadri": [
        "himadri"
    ],

    "Bharati": [
        "bharati"
    ],

    "Dakshin Gangotri": [
        "dakshin gangotri",
        "dakshin-gangotri"
    ]
}


def detect_stations(results):

    found = []

    for station, keywords in STATIONS.items():

        for keyword in keywords:

            mask = results[
                "search_text"
            ].str.contains(
                keyword,
                case=False,
                na=False,
                regex=False
            )

            if mask.any():

                found.append(station)
                break

    return found


# ============================================================
# REGION DETECTION
# ============================================================

def detect_regions(results):

    regions = []

    text = " ".join(
        results["search_text"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    if "arctic" in text:
        regions.append("Arctic")

    if "antarctic" in text:
        regions.append("Antarctica")

    if "svalbard" in text:
        if "Arctic" not in regions:
            regions.append("Arctic")

    return regions


# ============================================================
# RESEARCH AREA DETECTION
# ============================================================

RESEARCH_AREAS = {

    "Climate Change": [
        "climate change",
        "climate",
        "global warming",
        "paleoclimate",
        "paleoclimatic"
    ],

    "Atmospheric Science": [
        "atmosphere",
        "atmospheric",
        "aerosol",
        "black carbon",
        "greenhouse gas",
        "ghg",
        "ozone",
        "meteorological"
    ],

    "Glaciology": [
        "glacier",
        "glaciological",
        "ice sheet",
        "ice-shelf",
        "ice shelf",
        "snow",
        "cryosphere"
    ],

    "Oceanography": [
        "ocean",
        "oceanographic",
        "hydrographic",
        "marine",
        "fjord",
        "prydz bay",
        "sea water"
    ],

    "Geology": [
        "geology",
        "geological",
        "tectonic",
        "tectono",
        "rock",
        "mineral",
        "gneiss"
    ],

    "Biology & Ecology": [
        "biodiversity",
        "bacteria",
        "fungi",
        "phytoplankton",
        "diatom",
        "zooplankton",
        "ecosystem",
        "marine mammals",
        "sea birds"
    ],

    "Geomagnetism & Space Science": [
        "geomagnetic",
        "magnetic field",
        "magnetometer",
        "ionosphere",
        "infrasonic",
        "cosmic ray",
        "vlf"
    ],

    "Remote Sensing": [
        "remote sensing",
        "multispectral",
        "hyperspectral",
        "imagery"
    ]
}


def detect_research_areas(results):

    areas = []

    text = " ".join(
        results["search_text"]
        .fillna("")
        .astype(str)
        .tolist()
    )

    for area, keywords in RESEARCH_AREAS.items():

        for keyword in keywords:

            if keyword in text:

                areas.append(area)
                break

    return areas


# ============================================================
# YEAR EXTRACTION
# ============================================================

def extract_years(results):

    years = []

    columns = [
        "year",
        "publication_year",
        "website_year",
        "start_date",
        "end_date"
    ]

    for column in columns:

        if column not in results.columns:
            continue

        for value in results[column].dropna():

            matches = re.findall(
                r"\b(19\d{2}|20\d{2})\b",
                str(value)
            )

            for match in matches:

                year = int(match)

                if year not in years:
                    years.append(year)

    return sorted(years)


# ============================================================
# SOURCE BREAKDOWN
# ============================================================

def source_breakdown(results):

    if "source" not in results.columns:
        return {}

    return (
        results["source"]
        .fillna("Unknown")
        .value_counts()
        .to_dict()
    )


# ============================================================
# CONTENT TYPE BREAKDOWN
# ============================================================

def content_type_breakdown(results):

    if "content_type" not in results.columns:
        return {}

    return (
        results["content_type"]
        .fillna("Unknown")
        .value_counts()
        .to_dict()
    )


# ============================================================
# STATION BREAKDOWN
# ============================================================

def station_breakdown(results):

    counts = {}

    for station, keywords in STATIONS.items():

        count = 0

        for text in results[
            "search_text"
        ].fillna(""):

            text = str(text).lower()

            for keyword in keywords:

                if keyword in text:

                    count += 1
                    break

        if count > 0:
            counts[station] = count

    return counts


# ============================================================
# DISPLAY RESULT
# ============================================================

def display_record(number, row):

    title = get_title(row)

    source = row.get(
        "source",
        "Unknown"
    )

    content_type = row.get(
        "content_type",
        "Unknown"
    )

    source_file = row.get(
        "source_file",
        "Unknown"
    )

    print("\n----------------------------------------")
    print(f"RESULT {number}")
    print("----------------------------------------")

    print(f"Source: {source}")
    print(f"Type: {content_type}")
    print(f"Title: {title}")
    print(f"Data file: {source_file}")

    # Station
    if "station" in row.index:

        station = row["station"]

        if not pd.isna(station) and str(station).strip():

            print(
                f"Station: {station}"
            )

    # URL
    for column in [
        "metadata_url",
        "source_url",
        "profile_url",
        "download_url",
        "url"
    ]:

        if column not in row.index:
            continue

        value = row[column]

        if pd.isna(value):
            continue

        value = str(value).strip()

        if value:

            print(
                f"URL: {value}"
            )

            break


# ============================================================
# RESEARCH ANALYSIS
# ============================================================

def display_analysis(
    results,
    query,
    stations,
    regions,
    areas,
    years,
    sources,
    content_types
):

    print("\n")
    print("=" * 70)
    print("                    RESEARCH ANALYSIS")
    print("=" * 70)

    print(f"Topic: {query}")
    print(
        f"Unique records analyzed: {len(results)}"
    )

    # --------------------------------------------------------
    # SOURCES
    # --------------------------------------------------------

    print("\nSOURCES")

    if sources:

        for source, count in sources.items():

            percentage = (
                count / len(results)
            ) * 100

            print(
                f"- {source}: "
                f"{count} records "
                f"({percentage:.1f}%)"
            )

    else:

        print("- No source information")

    # --------------------------------------------------------
    # CONTENT TYPES
    # --------------------------------------------------------

    print("\nCONTENT TYPES")

    if content_types:

        for content_type, count in content_types.items():

            print(
                f"- {content_type}: {count}"
            )

    else:

        print("- No content type information")

    # --------------------------------------------------------
    # STATIONS
    # --------------------------------------------------------

    print("\nSTATIONS")

    if stations:

        for station in stations:
            print(f"- {station}")

    else:

        print("- No station references detected")

    # --------------------------------------------------------
    # GEOGRAPHIC FOCUS
    # --------------------------------------------------------

    print("\nGEOGRAPHIC FOCUS")

    if regions:

        for region in regions:
            print(f"- {region}")

    else:

        print("- No polar region detected")

    # --------------------------------------------------------
    # RESEARCH AREAS
    # --------------------------------------------------------

    print("\nRESEARCH AREAS")

    if areas:

        for area in areas:
            print(f"- {area}")

    else:

        print("- No major research areas detected")

    # --------------------------------------------------------
    # TIME RANGE
    # --------------------------------------------------------

    print("\nTIME PERIOD")

    if years:

        print(
            f"- {min(years)} to {max(years)}"
        )

    else:

        print(
            "- No publication/project years detected"
        )

    # --------------------------------------------------------
    # STATION DISTRIBUTION
    # --------------------------------------------------------

    print("\nSTATION DISTRIBUTION")

    counts = station_breakdown(results)

    if counts:

        for station, count in counts.items():

            percentage = (
                count / len(results)
            ) * 100

            print(
                f"- {station}: "
                f"{count} records "
                f"({percentage:.1f}%)"
            )

    else:

        print(
            "- No station-specific distribution available"
        )

    # --------------------------------------------------------
    # KEY EVIDENCE
    # --------------------------------------------------------

    print("\nKEY EVIDENCE")

    for number, (_, row) in enumerate(
        results.head(5).iterrows(),
        start=1
    ):

        title = get_title(row)

        source = row.get(
            "source",
            "Unknown"
        )

        print(
            f"{number}. {title}"
        )

        print(
            f"   Source: {source}"
        )

        if "station" in row.index:

            station = row["station"]

            if (
                not pd.isna(station)
                and str(station).strip()
            ):

                print(
                    f"   Station: {station}"
                )

    # --------------------------------------------------------
    # DATA-GROUNDED SYNTHESIS
    # --------------------------------------------------------

    print("\nRESEARCH SYNTHESIS")

    if len(results) == 0:

        print(
            "No relevant records were found."
        )

        return

    synthesis_parts = []

    if areas:

        synthesis_parts.append(
            "The retrieved evidence covers "
            + ", ".join(areas)
            + "."
        )

    if regions:

        synthesis_parts.append(
            "The geographic focus represented "
            "in the retrieved records includes "
            + ", ".join(regions)
            + "."
        )

    if stations:

        synthesis_parts.append(
            "Station-specific evidence is associated "
            "with "
            + ", ".join(stations)
            + "."
        )

    if years:

        synthesis_parts.append(
            f"The available dated records span "
            f"approximately {min(years)} to "
            f"{max(years)}."
        )

    # --------------------------------------------------------
    # Content-specific observation
    # --------------------------------------------------------

    if content_types:

        strongest_type = max(
            content_types,
            key=content_types.get
        )

        synthesis_parts.append(
            f"Among the retrieved records, "
            f"{strongest_type} is the most represented "
            f"content type."
        )

    synthesis_parts.append(
        "These observations are derived only from "
        "the retrieved primary datasets. The system "
        "does not claim scientific findings that are "
        "not explicitly represented in the source records."
    )

    for sentence in synthesis_parts:

        print(sentence)


# ============================================================
# SEARCH
# ============================================================

def search_research(df, query):

    keywords = extract_keywords(query)

    if not keywords:

        print(
            "\nPlease enter a meaningful research topic."
        )

        return

    # --------------------------------------------------------
    # Calculate relevance
    # --------------------------------------------------------

    df["score"] = df.apply(
        lambda row:
        calculate_score(
            row,
            keywords
        ),
        axis=1
    )

    # --------------------------------------------------------
    # Keep relevant records
    # --------------------------------------------------------

    results = df[
        df["score"] > 0
    ].copy()

    if len(results) == 0:

        print(
            "\nNo relevant records found."
        )

        return

    # --------------------------------------------------------
    # Sort
    # --------------------------------------------------------

    results = results.sort_values(
        by="score",
        ascending=False
    )

    # --------------------------------------------------------
    # Remove duplicate research
    # --------------------------------------------------------

    results = remove_duplicates(
        results
    )

    # --------------------------------------------------------
    # Limit results
    # --------------------------------------------------------

    results = results.head(
        TOP_RESULTS
    ).copy()

    # --------------------------------------------------------
    # Display
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("                    TOP RESEARCH FOUND")
    print("=" * 70)

    print(
        f"Found {len(results)} relevant unique records."
    )

    for number, (_, row) in enumerate(
        results.iterrows(),
        start=1
    ):

        display_record(
            number,
            row
        )

    # --------------------------------------------------------
    # ANALYSIS
    # --------------------------------------------------------

    stations = detect_stations(
        results
    )

    regions = detect_regions(
        results
    )

    areas = detect_research_areas(
        results
    )

    years = extract_years(
        results
    )

    sources = source_breakdown(
        results
    )

    content_types = content_type_breakdown(
        results
    )

    display_analysis(
        results,
        query,
        stations,
        regions,
        areas,
        years,
        sources,
        content_types
    )


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print("\n")
    print("=" * 70)
    print("              POLAR RESEARCH ANALYZER")
    print("=" * 70)

    print(
        "\nThis analyzer uses primary/verified CSV sources."
    )

    print(
        "\nDerived knowledge-base files are NOT used."
    )

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    df = load_primary_data()

    if df is None:
        return

    # --------------------------------------------------------
    # Create search text
    # --------------------------------------------------------

    df = create_search_text(
        df
    )

    print(
        "\nAnalyzer ready."
    )

    print(
        "\nAsk about polar research "
        "(type 'exit' to stop):"
    )

    # --------------------------------------------------------
    # Interactive loop
    # --------------------------------------------------------

    while True:

        query = input(
            "\n> "
        ).strip()

        if query.lower() == "exit":

            print(
                "\nGoodbye!"
            )

            break

        if query == "":

            print(
                "Please enter a research topic."
            )

            continue

        search_research(
            df.copy(),
            query
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()

