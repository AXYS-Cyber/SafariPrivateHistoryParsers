import plistlib
import csv
import base64

# Ask user for input/output file paths
plist_file = input("Enter path to the plist file: ").strip('"')
csv_file = input("Enter path for the output CSV file: ").strip('"')

# Read plist
with open(plist_file, "rb") as f:
    plist_data = plistlib.load(f)

# Navigate to SessionHistory → SessionHistoryEntries
entries = plist_data.get("SessionHistory", {}).get("SessionHistoryEntries", [])

# Define CSV column names
fieldnames = [
    "SessionHistoryEntryTitle",
    "SessionHistoryEntryURL",
    "SessionHistoryEntryOriginalURL",
    "SessionHistoryEntryShouldOpenExternalURLsPolicyKey",
    "SessionHistoryEntryData_Base64",
    "SessionHistoryEntryData_DecodedText"
]

with open(csv_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for entry in entries:
        row = {
            "SessionHistoryEntryTitle": entry.get("SessionHistoryEntryTitle"),
            "SessionHistoryEntryURL": entry.get("SessionHistoryEntryURL"),
            "SessionHistoryEntryOriginalURL": entry.get("SessionHistoryEntryOriginalURL"),
            "SessionHistoryEntryShouldOpenExternalURLsPolicyKey": entry.get("SessionHistoryEntryShouldOpenExternalURLsPolicyKey"),
            "SessionHistoryEntryData_Base64": entry.get("SessionHistoryEntryData"),
        }

        # Try decoding the <data> field as UTF-16 text (Safari often stores state this way)
        decoded_text = None
        try:
            decoded_text = base64.b64decode(entry.get("SessionHistoryEntryData")).decode("utf-16", errors="ignore")
        except Exception:
            pass
        row["SessionHistoryEntryData_DecodedText"] = decoded_text

        writer.writerow(row)

print(f"\n✅ Exported {len(entries)} session entries from {plist_file} → {csv_file}")
