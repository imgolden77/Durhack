import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_connection():
    conn = sqlite3.connect('vehicles.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/years")
def get_years():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT year FROM vehicles")
    years = [row['year'] for row in cursor.fetchall()]
    conn.close()
    return {"years": years}

@app.get("/makes")
def get_makes(year: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT make FROM vehicles WHERE year = ? ORDER BY make ASC", (year,))
    makes = [row['make'] for row in cursor.fetchall()]
    conn.close()
    return {"makes": makes}

@app.get("/models")
def get_models(year: int, make: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT model FROM vehicles WHERE year = ? AND make = ? ORDER BY model ASC", (year, make))
    models = [row['model'] for row in cursor.fetchall()]
    conn.close()
    return {"models": models}

@app.get("/results")
def get_results(year: int, make: str, model: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT model, comb08, city08, highway08, fuelType1, displ, trany
        FROM vehicles 
        WHERE year = ? AND make = ? AND model = ?
    """
    cursor.execute(query, (year, make, model))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"results": results}