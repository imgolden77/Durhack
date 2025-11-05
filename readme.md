# Drive Wise (Durhack)

## Short description
- Drive Wise is a simple demo that uses vehicle fuel-efficiency data and EIA weekly fuel prices to estimate fuel volume and trip cost. Frontend is a single HTML file with a Leaflet map; backend is a FastAPI app (main2.py).

## Prerequisites
- Python 3.10+
- Optional: ngrok (for sharing)
- Required Python packages: fastapi, uvicorn, python-dotenv, requests

## Environment
- Create a `.env` in the project root or export variables:
  - `EIA_KEY=your_eia_api_key`
  - `ORS_API_KEY=your_ors_api_key`

## Quick start (local)
1. Create and activate virtualenv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```


## Install dependencies:
    ```bash
    pip install fastapi uvicorn python-dotenv requests
    ```
## Run server:
```bash
uvicorn main2:app --host 0.0.0.0 --port 8000 --reload
```
## Open in browser:
Local: http://127.0.0.1:8000/
If using ngrok, run ngrok http 8000 and open the HTTPS URL ngrok provides.
Notes for sharing (ngrok)

Share the HTTPS ngrok URL (e.g. https://xxxx.ngrok-free.dev). The frontend uses window.location.origin for API calls so the same URL serves pages and API.
Free ngrok URLs are temporary and change each session.

## Key endpoints

```bash
GET /years
GET /makes?year=YYYY
GET /models?year=YYYY&make=NAME
GET /results?year=...&make=...&model=...
GET /fuel-price?grade=regular|midgrade|premium|diesel
POST /trip-quote (json: { miles, mpg, grade })
```