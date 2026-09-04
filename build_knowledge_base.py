
import pandas as pd
import os


# ==========================================
# POLAR KNOWLEDGE BASE BUILDER
# ==========================================

print("==========================================")
print("     BUILDING POLAR KNOWLEDGE BASE")
print("==========================================")


# ==========================================
# FUNCTION TO LOAD CSV
# ==========================================

def load_csv(filename, source):

    if not os.path.exists(filename):

        print("NOT FOUND:", filename)
        return pd.DataFrame()

    try:

        df = pd.read_csv(
            filename,
            encoding="utf-8-sig"
        )

        print(
            "LOADED:",
            filename,
            "|",
            len(df),
            "rows"
        )

        # Add source column
        df["source"] = source

        return df

    except Exception as e:

        print(
            "ERROR loading",
            filename,
            ":",
            e
        )

        return pd.DataFrame()


# ==========================================
# LOAD NCPOR DATA
# ==========================================

print("\n--- NCPOR DATA ---")

arctic_projects = load_csv(
    "arctic_projects.csv",
    "NCPOR"
)

arctic_team = load_csv(
    "arctic_team_members.csv",
    "NCPOR"
)

polar_images = load_csv(
    "polar_images.csv",
    "NCPOR"
)

polar_publications = load_csv(
    "polar_publications.csv",
    "NCPOR"
)

southern_ocean = load_csv(
    "polar_southern_ocean_reports.csv",
    "NCPOR"
)


# ==========================================
# LOAD NPDC DATA
# ==========================================

print("\n--- NPDC DATA ---")

npdc = load_csv(
    "npdc_prototype.csv",
    "NPDC"
)


# ==========================================
# ADD CONTENT TYPE
# ==========================================

arctic_projects["content_type"] = "Arctic Project"

arctic_team["content_type"] = "Team Member"

polar_images["content_type"] = "Image"

polar_publications["content_type"] = "Publication"

southern_ocean["content_type"] = "Southern Ocean Report"

npdc["content_type"] = "Scientific Dataset"


# ==========================================
# COMBINE ALL DATA
# ==========================================

print("\n--- COMBINING DATA ---")


all_data = pd.concat(
    [
        arctic_projects,
        arctic_team,
        polar_images,
        polar_publications,
        southern_ocean,
        npdc
    ],
    ignore_index=True,
    sort=False
)


# ==========================================
# CLEAN DATA
# ==========================================

all_data = all_data.fillna("")


# Remove completely empty rows

all_data = all_data[
    all_data.astype(str)
    .apply(
        lambda row: row.str.strip().ne("").any(),
        axis=1
    )
]


# ==========================================
# SAVE MASTER FILE
# ==========================================

output_file = "polar_knowledge_base.csv"


all_data.to_csv(
    output_file,
    index=False,
    encoding="utf-8-sig"
)


# ==========================================
# FINAL REPORT
# ==========================================

print("\n==========================================")
print("       KNOWLEDGE BASE CREATED")
print("==========================================")

print(
    "TOTAL RECORDS:",
    len(all_data)
)

print(
    "TOTAL COLUMNS:",
    len(all_data.columns)
)

print(
    "FILE:",
    output_file
)


# ==========================================
# CONTENT BREAKDOWN
# ==========================================

print("\nCONTENT BREAKDOWN:")

print(
    all_data["content_type"]
    .value_counts()
)


print("\nSOURCE BREAKDOWN:")

print(
    all_data["source"]
    .value_counts()
)


# ==========================================
# PREVIEW
# ==========================================

print("\nFIRST 10 RECORDS:")

print(
    all_data[
        ["source", "content_type"]
    ].head(10).to_string(
        index=False
    )
)

print("\n==========================================")
print("DONE!")
print("==========================================")
