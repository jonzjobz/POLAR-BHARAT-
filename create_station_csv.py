import pandas as pd
import re

# ==========================================
# SETTINGS
# ==========================================

INPUT_FILE = "polar_knowledge_base.csv"
OUTPUT_FILE = "polar_station_data.csv"
SUMMARY_FILE = "station_summary.csv"

STATIONS = {
    "Maitri": [
        r"\bmaitri\b",
        r"\bmaitri station\b",
        r"\bindian antarctic station maitri\b"
    ],

    "Himadri": [
        r"\bhimadri\b",
        r"\bhimadri station\b",
        r"\bindian arctic station himadri\b"
    ],

    "Bharati": [
        r"\bbharati\b",
        r"\bbharati station\b",
        r"\bindian antarctic station bharati\b"
    ],

    "Dakshin Gangotri": [
        r"\bdakshin gangotri\b",
        r"\bdakshin-gangotri\b",
        r"\bdakshin gangotri station\b"
    ]
}


# ==========================================
# LOAD KNOWLEDGE BASE
# ==========================================

print("=" * 42)
print("      CREATING STATION DATA")
print("=" * 42)

print("\nLoading knowledge base...")

df = pd.read_csv(INPUT_FILE)

print("Knowledge base loaded:", len(df), "records")
print("Columns found:", len(df.columns))


# ==========================================
# PREPARE SEARCH TEXT
# ==========================================

print("\nPreparing records for station detection...")

# Combine ALL columns into one searchable text field.
# NaN values are replaced with empty strings.

search_columns = list(df.columns)

df["_search_text"] = (
    df[search_columns]
    .fillna("")
    .astype(str)
    .agg(" ".join, axis=1)
    .str.lower()
)


# ==========================================
# DETECT STATIONS
# ==========================================

print("\nSearching for station references...")

station_rows = []

for index, row in df.iterrows():

    text = row["_search_text"]

    matched_stations = []

    for station, patterns in STATIONS.items():

        found = False

        for pattern in patterns:

            if re.search(pattern, text, flags=re.IGNORECASE):
                found = True
                break

        if found:
            matched_stations.append(station)

    # --------------------------------------
    # CREATE ONE ROW PER MATCHED STATION
    # --------------------------------------

    for station in matched_stations:

        new_row = row.drop(labels=["_search_text"]).to_dict()

        new_row["station"] = station

        # Determine region
        if station == "Himadri":
            new_row["arctic_or_antarctic"] = "Arctic"
        else:
            new_row["arctic_or_antarctic"] = "Antarctica"

        station_rows.append(new_row)


# ==========================================
# CREATE DATAFRAME
# ==========================================

station_df = pd.DataFrame(station_rows)


# ==========================================
# REMOVE DUPLICATES
# ==========================================

if not station_df.empty:

    before = len(station_df)

    # A record is duplicate only when the
    # SAME source record was assigned to the
    # SAME station.

    duplicate_columns = [
        col for col in station_df.columns
        if col not in ["station", "arctic_or_antarctic"]
    ]

    station_df = station_df.drop_duplicates(
        subset=["station"] + duplicate_columns
    )

    after = len(station_df)

    print("\nDuplicate records removed:", before - after)

else:

    print("\nNo station records detected.")


# ==========================================
# REORDER COLUMNS
# ==========================================

if not station_df.empty:

    columns = station_df.columns.tolist()

    preferred_columns = [
        "station",
        "arctic_or_antarctic",
        "source",
        "content_type",
        "title",
        "category",
        "subcategory",
        "metadata_url"
    ]

    ordered_columns = []

    for col in preferred_columns:

        if col in columns:
            ordered_columns.append(col)

    for col in columns:

        if col not in ordered_columns:
            ordered_columns.append(col)

    station_df = station_df[ordered_columns]


# ==========================================
# SAVE STATION DATA
# ==========================================

station_df.to_csv(
    OUTPUT_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================
# STATION BREAKDOWN
# ==========================================

print("\n" + "=" * 42)
print("       STATION DATA CREATED")
print("=" * 42)

print("\nFILE:", OUTPUT_FILE)
print("TOTAL STATION RECORDS:", len(station_df))

print("\n" + "=" * 42)
print("        STATION BREAKDOWN")
print("=" * 42)

for station in STATIONS.keys():

    count = len(
        station_df[
            station_df["station"] == station
        ]
    )

    print(station, ":", count, "records")


# ==========================================
# CREATE STATION SUMMARY
# ==========================================

summary_rows = []

for station in STATIONS.keys():

    station_data = station_df[
        station_df["station"] == station
    ]

    summary_rows.append({

        "station": station,

        "arctic_or_antarctic":
            "Arctic" if station == "Himadri"
            else "Antarctica",

        "total_records":
            len(station_data),

        "arctic_projects":
            len(
                station_data[
                    station_data["content_type"]
                    == "Arctic Project"
                ]
            ),

        "scientific_datasets":
            len(
                station_data[
                    station_data["content_type"]
                    == "Scientific Dataset"
                ]
            ),

        "publications":
            len(
                station_data[
                    station_data["content_type"]
                    == "Publication"
                ]
            ),

        "southern_ocean_reports":
            len(
                station_data[
                    station_data["content_type"]
                    == "Southern Ocean Report"
                ]
            ),

        "images":
            len(
                station_data[
                    station_data["content_type"]
                    == "Image"
                ]
            ),

        "team_members":
            len(
                station_data[
                    station_data["content_type"]
                    == "Team Member"
                ]
            )
    })


summary_df = pd.DataFrame(summary_rows)

summary_df.to_csv(
    SUMMARY_FILE,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================
# DISPLAY SUMMARY
# ==========================================

print("\n" + "=" * 42)
print("       STATION SUMMARY CREATED")
print("=" * 42)

print("\nFILE:", SUMMARY_FILE)

print("\nSUMMARY:\n")

print(
    summary_df.to_string(index=False)
)


# ==========================================
# PREVIEW
# ==========================================

print("\n" + "=" * 42)
print("       FIRST 10 STATION RECORDS")
print("=" * 42)

if len(station_df) > 0:

    preview_columns = [
        col for col in [
            "station",
            "source",
            "content_type",
            "title",
            "category",
            "subcategory"
        ]
        if col in station_df.columns
    ]

    print(
        station_df[
            preview_columns
        ].head(10).to_string(index=False)
    )

else:

    print("No station records found.")


# ==========================================
# FINAL
# ==========================================

print("\n" + "=" * 42)
print("       STATION PROCESSING COMPLETE")
print("=" * 42)

print("\nCreated files:")
print("1.", OUTPUT_FILE)
print("2.", SUMMARY_FILE)

print("\n" + "=" * 42)