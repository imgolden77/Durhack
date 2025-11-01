import os
import sys
import pandas as pd
import sqlite3
import time

csv_file_path = 'vehicles.csv'
db_file_path = 'vehicles.db' 
table_name = 'vehicles'  
chunk_size = 50000

conn = sqlite3.connect(db_file_path)
print("Database connection established.")

start_time = time.time()
print("Starting CSV to SQLite conversion...")

try:
    for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size):
        chunk.to_sql(name=table_name, con=conn, if_exists='append', index=False)
        print(f"Inserted chunk of size {len(chunk)} into the database.")
except Exception as e:
    print(f"An error occurred: {e}")
    
finally:
    conn.close()
    print("Database connection closed.")

end_time = time.time()
print("\n Conversion complete!")
print(f"total time consumption: {end_time - start_time:.2f} 초")
print(f"Now use '{db_file_path}' file in the app.")