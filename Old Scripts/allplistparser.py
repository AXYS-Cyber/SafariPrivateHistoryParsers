import plistlib
import csv
import base64
import os

# Ask user for input/output folder
input_dir = input("Enter path to folder containing plist files: ").strip('"')
output_dir = input("Enter path for output CSV files: ").strip('"')

# Create output folder if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Scan for all plist files
plist_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.plist')]

for plist_filename in plist_files:
    plist_path = os.path.join(input_dir, plist_filename)
    
    # Read plist
    with open(plist_path, "rb") as f:
        plist_data = plistlib.load(f)

    # Navigate to SessionHistory → SessionHistoryEntries
    entries = plist_data.get("SessionHistory", {}).get("SessionHistoryEntries", [])

    if not entries:
        print(f"⚠️ No session entries found in {plist_filename}, skipping.")
        continue

    # Output CSV file (same base name as plist)
    csv_filename = os.path.splitext(plist_filename)[0] + ".csv"
    csv_path = os.path.join(output_dir, csv_filename)

    # Define CSV columns
    fieldnames = [
        "SessionHistoryEntryTitle",
        "SessionHistoryEntryURL",
        "SessionHistoryEntryOriginalURL",
        "SessionHistoryEntryShouldOpenExternalURLsPolicyKey",
        "SessionHistoryEntryData_Base64",
        "SessionHistoryEntryData_DecodedText"
    ]

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=":")  # fixed delimiter
        writer.writeheader()

        for entry in entries:
            row = {
                "SessionHistoryEntryTitle": entry.get("SessionHistoryEntryTitle"),
                "SessionHistoryEntryURL": entry.get("SessionHistoryEntryURL"),
                "SessionHistoryEntryOriginalURL": entry.get("SessionHistoryEntryOriginalURL"),
                "SessionHistoryEntryShouldOpenExternalURLsPolicyKey": entry.get("SessionHistoryEntryShouldOpenExternalURLsPolicyKey"),
                "SessionHistoryEntryData_Base64": entry.get("SessionHistoryEntryData"),
            }

            # Try decoding the <data> field as UTF-16 text
            decoded_text = None
            try:
                decoded_text = base64.b64decode(entry.get("SessionHistoryEntryData")).decode("utf-16", errors="ignore")
            except Exception:
                pass
            row["SessionHistoryEntryData_DecodedText"] = decoded_text

            writer.writerow(row)

    print(f"✅ Exported {len(entries)} session entries from {plist_filename} → {csv_filename}")

print("\nAll plist files processed.")
