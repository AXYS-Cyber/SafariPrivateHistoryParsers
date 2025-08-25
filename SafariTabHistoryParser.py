import sqlite3
import os
import plistlib
import csv
import base64

def normalize_path(path: str) -> str:
    return os.path.normpath(path.strip('"'))

# Target directory containing SafariTabs.db 
input_folder = normalize_path(input("Enter folder containing SafariTabs.db. If running from same directory you may just press '[enter]': "))

db_path = os.path.join(input_folder, "SafariTabs.db")
if not os.path.isfile(db_path):
    print(f"❌ Could not find SafariTabs.db in {input_folder}")
    exit(1)

# Connect read-only
uri = f"file:{db_path}?mode=ro"
try:
    conn = sqlite3.connect(uri, uri=True)
except sqlite3.OperationalError as e:
    print(f"❌ Could not open database: {e}")
    exit(1)

cursor = conn.cursor()

#  Ask for output folder 
while True:
    output_dir = normalize_path(input("Enter output folder path. If running from same directory, no directory path is required: "))
    if not os.path.exists(output_dir):
        choice = input(f"⚠️ Folder '{output_dir}' does not exist. Create it? (y/n): ").lower()
        if choice == "y":
            try:
                os.makedirs(output_dir, exist_ok=True)
                break
            except Exception as e:
                print(f"❌ Could not create folder: {e}")
                continue
        else:
            print("Please enter another path.")
            continue
    else:
        break

#  Create subdirectories 
primary_dir = os.path.join(output_dir, "PrimaryPlists")
session_dir = os.path.join(output_dir, "SessionStatePlists")
os.makedirs(primary_dir, exist_ok=True)
os.makedirs(session_dir, exist_ok=True)

#  Log file 
log_path = os.path.join(output_dir, "extraction_log.txt")
log = open(log_path, "w", encoding="utf-8")

#  Extracts primary BPlists from bookmarks.local_attributes 
try:
    cursor.execute("SELECT rowid, local_attributes FROM bookmarks")
    rows = cursor.fetchall()
except sqlite3.OperationalError as e:
    print(f"❌ Failed to query bookmarks table: {e}")
    exit(1)

primary_count = 0
secondary_count = 0
csv_count = 0

#  CSV 
csv_path = os.path.join(output_dir, "All_SessionHistoryEntries.csv")
fieldnames = [
    "RowID",
    "SessionHistoryEntriesID",
    "SessionHistoryEntryTitle",
    "SessionHistoryEntryURL",
    "SessionHistoryEntryOriginalURL",
    "SessionHistoryEntryShouldOpenExternalURLsPolicyKey"
]

csvfile = open(csv_path, "w", newline="", encoding="utf-8")
writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter="|")
writer.writeheader()

#  Processes each row of bookmarks.local_attributes column
for rowid, blob_data in rows:
    if not isinstance(blob_data, (bytes, bytearray)):
        continue

    #  Saves bplist from BLOB entry
    primary_plist_path = os.path.join(primary_dir, f"{rowid}.plist")
    with open(primary_plist_path, "wb") as f:
        f.write(blob_data)
    primary_count += 1
    log.write(f"[PRIMARY] Extracted rowid {rowid} → {primary_plist_path}\n")
    print(f"[PRIMARY] Extracted rowid {rowid}")

    #  Load primary bplist from BLOB output
    try:
        with open(primary_plist_path, "rb") as f:
            primary_plist = plistlib.load(f)
    except Exception as e:
        log.write(f"[ERROR] Could not parse primary plist {rowid}: {e}\n")
        print(f"[ERROR] Could not parse primary plist {rowid}: {e}")
        continue

    session_blob = primary_plist.get("SessionState")
    if not isinstance(session_blob, (bytes, bytearray)):
        log.write(f"[WARN] No valid SessionState in {rowid}\n")
        print(f"[WARN] No valid SessionState in {rowid}")
        continue

    #  Trim anything before bplist header in SessionState key 
    magic_index = session_blob.find(b"bplist")
    if magic_index == -1:
        log.write(f"[WARN] No bplist header found in SessionState for rowid {rowid}\n")
        print(f"[WARN] No bplist header found in SessionState for rowid {rowid}")
        continue
    elif magic_index > 0:
        log.write(f"[INFO] Trimmed {magic_index} byte(s) before bplist in SessionState for rowid {rowid}\n")
        print(f"[INFO] Trimmed {magic_index} byte(s) before bplist in SessionState for rowid {rowid}")
        session_blob = session_blob[magic_index:]

    #  Saves as secondary plist 
    secondary_plist_path = os.path.join(session_dir, f"{rowid}_SessionState.plist")
    try:
        with open(secondary_plist_path, "wb") as f:
            f.write(session_blob)
        secondary_count += 1
        log.write(f"[SECONDARY] Extracted SessionState for rowid {rowid} → {secondary_plist_path}\n")
        print(f"[SECONDARY] Extracted SessionState for rowid {rowid}")
    except Exception as e:
        log.write(f"[ERROR] Could not write secondary plist for {rowid}: {e}\n")
        print(f"[ERROR] Could not write secondary plist for {rowid}: {e}")
        continue

    #  Loads secondary (output) bplist 
    try:
        with open(secondary_plist_path, "rb") as f:
            secondary_plist = plistlib.load(f)
    except Exception as e:
        log.write(f"[ERROR] Could not parse secondary plist {rowid}: {e}\n")
        print(f"[ERROR] Could not parse secondary plist {rowid}: {e}")
        continue

    #  Processes SessionHistoryEntries from SessionState key bplist
    entries = secondary_plist.get("SessionHistory", {}).get("SessionHistoryEntries", [])
    if not entries:
        log.write(f"[WARN] No session entries in {secondary_plist_path}\n")
        print(f"[WARN] No session entries in {secondary_plist_path}")
        continue

    for idx, entry in enumerate(entries):
        entry_id = idx # SessionHistoryEntries value from secondart bplist
        row = {
            "RowID": rowid,
            "SessionHistoryEntriesID": entry_id,
            "SessionHistoryEntryTitle": entry.get("SessionHistoryEntryTitle", ""),
            "SessionHistoryEntryURL": entry.get("SessionHistoryEntryURL", ""),
            "SessionHistoryEntryOriginalURL": entry.get("SessionHistoryEntryOriginalURL", ""),
            "SessionHistoryEntryShouldOpenExternalURLsPolicyKey": entry.get("SessionHistoryEntryShouldOpenExternalURLsPolicyKey", "")
        }
        writer.writerow(row)

    csv_count += 1
    log.write(f"[CSV] Appended {len(entries)} session entries from {secondary_plist_path} → {csv_path}\n")
    print(f"[CSV] Appended {len(entries)} session entries for rowid {rowid}")

#  Summary output at completion
summary = (
    f"\n✅ Completed extraction\n"
    f"Primary plists: {primary_count}\n"
    f"Secondary plists: {secondary_count}\n"
    f"CSV files: 1\n"
)
print(summary)
log.write(summary)
log.close()
csvfile.close()
conn.close()