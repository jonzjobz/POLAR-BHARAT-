import pandas as pd
import os

print("=" * 70)
print("          POLAR DATASET INSPECTION")
print("=" * 70)

# All CSV files in the current folder
csv_files = [f for f in os.listdir(".") if f.lower().endswith(".csv")]

if not csv_files:
    print("\nNo CSV files found in this folder.")
    exit()

print(f"\nCSV FILES FOUND: {len(csv_files)}")

for file in sorted(csv_files):

    print("\n" + "=" * 70)
    print(f"FILE: {file}")
    print("=" * 70)

    try:
        df = pd.read_csv(file)

        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")

        print("\nCOLUMNS:")
        for column in df.columns:
            print(f"  - {column}")

        print("\nMISSING VALUES:")
        missing = df.isnull().sum()

        for column, count in missing.items():
            if count > 0:
                print(f"  - {column}: {count}")

        print("\nDUPLICATE ROWS:")
        print(f"  {df.duplicated().sum()}")

        print("\nFIRST RECORD:")
        if len(df) > 0:
            for column in df.columns:
                value = df.iloc[0][column]

                # Keep huge metadata from flooding the terminal
                if pd.isna(value):
                    value = ""

                value = str(value)

                if len(value) > 300:
                    value = value[:300] + "... [truncated]"

                print(f"  {column}: {value}")

    except Exception as e:
        print(f"ERROR READING FILE: {e}")

print("\n" + "=" * 70)
print("          INSPECTION COMPLETE")
print("=" * 70)
