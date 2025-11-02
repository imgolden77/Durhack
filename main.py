import os
import time
import sqlite3
from typing import Dict, List, Literal, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

load_dotenv()
EIA_KEY = "En4wAHNIFd5JCKPrulq1FObHaU1mrcn9FtY6uhWZ"
if not EIA_KEY:
    raise RuntimeError("Missing EIA_KEY in environment (.env)")

app = FastAPI(title="Fuel Cost API")

# Allow local file and common dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "*",  # if opening index.html as file:// this helps in dev
    ],
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

# -----------------------------
# EIA / Pricing
# -----------------------------
PRODUCT_LABELS = {
    "EPMR": "regular",   # Regular
    "EPMS": "midgrade",  # Midgrade
    "EPMG": "premium",   # Premium
    "EPDD": "diesel",    # Diesel
}
LABEL_TO_CODE = {v: k for k, v in PRODUCT_LABELS.items()}

_cache: dict = {}
CACHE_TTL = 60 * 30  # 30 minutes

def fetch_eia_latest() -> dict:
    url = (
        "https://api.eia.gov/v2/petroleum/pri/gnd/data/"
        f"?api_key={EIA_KEY}"
        "&frequency=weekly&data[0]=value"
        "&sort[0][column]=period&sort[0][direction]=desc"
        "&offset=0&length=5000"
    )
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"EIA error {r.status_code}: {r.text[:120]}")
    data = r.json().get("response", {}).get("data", [])
    if not data:
        raise HTTPException(status_code=502, detail="No fuel price data returned from EIA")
    latest_date = data[0]["period"]
    latest = {"date": latest_date, "prices": {}}
    seen = set()
    for item in data:
        if item["period"] != latest_date:
            break
        code = item.get("product")
        if code in PRODUCT_LABELS and code not in seen:
            seen.add(code)
            latest["prices"][PRODUCT_LABELS[code]] = float(item["value"])  # USD/gal
    return latest


def get_prices_cached() -> dict:
    now = time.time()
    entry = _cache.get("eia")
    if entry and (now - entry["ts"] < CACHE_TTL):
        return entry["data"]
    data = fetch_eia_latest()
    _cache["eia"] = {"ts": now, "data": data}
    return data


# -----------------------------
# Fuel price + trip quote
# -----------------------------
@app.get("/fuel-price")
def fuel_price(grade: Literal["regular", "midgrade", "premium", "diesel"] = "regular"):
    data = get_prices_cached()
    price = data["prices"].get(grade)
    if price is None:
        raise HTTPException(status_code=404, detail=f"No price for grade={grade}")
    return {"grade": grade, "price_usd_per_gallon": price, "date": data["date"]}


class TripQuoteIn(BaseModel):
    miles: float
    mpg: float
    grade: Literal["regular", "midgrade", "premium", "diesel"] = "regular"
    return_gbp: bool = False
    usd_to_gbp: Optional[float] = None  # optional FX if you want GBP


@app.post("/trip-quote")
def trip_quote(body: TripQuoteIn):
    if body.miles <= 0 or body.mpg <= 0:
        raise HTTPException(status_code=400, detail="miles and mpg must be positive")
    data = get_prices_cached()
    price = data["prices"].get(body.grade)
    if price is None:
        raise HTTPException(status_code=404, detail=f"No price for grade={body.grade}")

    gallons = body.miles / body.mpg
    cost_usd = gallons * price

    result = {
        "miles": body.miles,
        "mpg": body.mpg,
        "grade": body.grade,
        "price_usd_per_gallon": price,
        "date": data["date"],
        "gallons": round(gallons, 6),
        "cost_usd": round(cost_usd, 2),
    }
    if body.return_gbp and body.usd_to_gbp:
        result["cost_gbp"] = round(cost_usd * body.usd_to_gbp, 2)
    return result
