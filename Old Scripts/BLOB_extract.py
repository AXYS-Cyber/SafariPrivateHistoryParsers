import sqlite3
import os

# Ask user for inputs
db_path = input("Enter path to the SQLite database: ").strip('"')
table_name = input("Enter the table name: ").strip()
column_name = input("Enter the BLOB column name: ").strip()
output_dir = input("Enter output folder path: ").strip('"')

# Create output folder if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Connect to DB
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query all rows from the table
cursor.execute(f"SELECT rowid, {column_name} FROM {table_name}")

count = 0
for rowid, blob_data in cursor.fetchall():
    if blob_data is None:
        continue

    # Choose an output filename (rowid as identifier)
    out_file = os.path.join(output_dir, f"{table_name}_{rowid}.bin")

    with open(out_file, "wb") as f:
        f.write(blob_data)
    count += 1

print(f"✅ Extracted {count} BLOBs from table '{table_name}' into {output_dir}")

conn.close()
