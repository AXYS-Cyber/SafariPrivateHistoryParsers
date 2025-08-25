import sqlite3
import os

# --- Helper to normalize Windows paths ---
def normalize_path(path: str) -> str:
    # Remove surrounding quotes if user pastes "C:\path"
    return os.path.normpath(path.strip('"'))

# Ask user for database path
db_path = normalize_path(input("Enter path to the SQLite database: "))

# Connect in read-only mode
uri = f"file:{db_path}?mode=ro"
try:
    conn = sqlite3.connect(uri, uri=True)
except sqlite3.OperationalError as e:
    print(f"❌ Could not open database: {e}")
    exit(1)

cursor = conn.cursor()

# List available tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
if not tables:
    print("❌ No tables found in this database.")
    conn.close()
    exit(1)

print("\n📋 Available tables:")
for i, t in enumerate(tables, 1):
    print(f"  {i}. {t}")

# Ask user for table name (or select by number)
table_input = input("\nEnter the table name (or number): ").strip()
if table_input.isdigit() and 1 <= int(table_input) <= len(tables):
    table_name = tables[int(table_input) - 1]
else:
    table_name = table_input

# List available columns in that table
cursor.execute(f"PRAGMA table_info({table_name});")
columns = [c[1] for c in cursor.fetchall()]
if not columns:
    print(f"❌ No columns found in table '{table_name}'.")
    conn.close()
    exit(1)

print(f"\n📋 Columns in table '{table_name}':")
for i, c in enumerate(columns, 1):
    print(f"  {i}. {c}")

# Ask user for column name (or select by number)
col_input = input("\nEnter the column name (or number): ").strip()
if col_input.isdigit() and 1 <= int(col_input) <= len(columns):
    column_name = columns[int(col_input) - 1]
else:
    column_name = col_input

# Ask for output folder, confirm creation if missing
while True:
    output_dir = normalize_path(input("\nEnter output folder path: "))
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

# Query all rows from the chosen table/column
try:
    cursor.execute(f"SELECT rowid, {column_name} FROM {table_name}")
except sqlite3.OperationalError as e:
    print(f"❌ SQL error: {e}")
    conn.close()
    exit(1)

count = 0
for rowid, blob_data in cursor.fetchall():
    if blob_data is None:
        continue

    # Default extension
    ext = ".bin"

    # Check if it starts with "bplist"
    if blob_data.startswith(b"bplist"):
        ext = ".plist"

    # Choose an output filename (rowid as identifier)
    out_file = os.path.join(output_dir, f"{table_name}_{rowid}{ext}")

    # Write to file
    with open(out_file, "wb") as f:
        f.write(blob_data)

    count += 1

print(f"\n✅ Extracted {count} BLOB(s) from table '{table_name}' into {output_dir}")
conn.close()
