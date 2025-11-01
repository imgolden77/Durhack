import sqlite3
conn = sqlite3.connect('vehicles.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

target_make = "Hyundai"
target_year = 2024

query = "SELECT * FROM vehicles WHERE make = ? AND year = ?"
cursor.execute(query, (target_make, target_year))
rows = cursor.fetchall()

print(f"Vehicles from {target_make} in {target_year}:\n")
for row in rows:
    print(dict(row))

conn.close()
