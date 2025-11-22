# Multi-Agent Tourism System

A FastAPI-based multi-agent system that orchestrates two child agents (Weather and Places) using open-source APIs. It parses natural language inputs like:

- “I’m going to go to Bangalore, let’s plan my trip.”
- “I’m going to go to Bangalore, what is the temperature there?”
- “I’m going to go to Bangalore, what is the temperature there? And what are the places I can visit?”

and responds using live data from Nominatim (geocoding), Open‑Meteo (weather), and Overpass (tourist attractions from OpenStreetMap).

## Features
- Parent Orchestrator agent parses your intent and routes to child agents
  - Weather Agent (Open‑Meteo)
  - Places Agent (Overpass / OpenStreetMap)
- Graceful handling for unknown/non-existent places: “It doesn’t know this place exist”
- Simple web UI to enter your query and view responses

## Tech Stack
- FastAPI
- httpx (async HTTP client)
- Jinja2 (FastAPI default templating-compatible; UI is static HTML/JS)
- Vanilla HTML/CSS/JS for the frontend

## Project Structure
```
multi agent tourism/
├─ app/
│  ├─ __init__.py
│  ├─ main.py                 # FastAPI app + orchestrator
│  └─ services/
│     ├─ __init__.py
│     ├─ geocoding.py         # Nominatim
│     ├─ weather.py           # Open‑Meteo
│     └─ places.py            # Overpass (OSM)
├─ static/
│  ├─ index.html              # Minimal UI
│  ├─ app.js
│  └─ style.css
├─ requirements.txt
└─ README.md
```

## APIs Used
- Geocoding: Nominatim Search API
  - Base: https://nominatim.openstreetmap.org/search
  - Docs: https://nominatim.org/release-docs/develop/api/Search/
- Weather: Open‑Meteo Forecast API
  - Endpoint: https://api.open-meteo.com/v1/forecast
  - Docs: https://open-meteo.com/en/docs
- Places: Overpass API (OpenStreetMap data)
  - Base: https://overpass-api.de/api/interpreter
  - Docs: https://wiki.openstreetmap.org/wiki/Overpass_API

## Setup
1) Python 3.10+
2) Create and activate a virtual environment (recommended)

On Windows (PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3) Install dependencies
```
pip install -r requirements.txt
```

## Run
Start the FastAPI app with Uvicorn:
```
uvicorn app.main:app --reload --port 8000
```
Open your browser to:
```
http://127.0.0.1:8000/
```

## Usage Examples
- Input: "I’m going to go to Bangalore, let’s plan my trip."
  - Output: A list of up to 5 attractions in Bangalore (Lalbagh, Cubbon Park, etc.)
- Input: "I’m going to go to Bangalore, what is the temperature there"
  - Output: e.g., "In Bangalore it’s currently 24°C with a chance of 35% to rain."
- Input: "I’m going to go to Bangalore, what is the temperature there? And what are the places I can visit?"
  - Output: Combined weather summary and attractions list

## Notes
- This project uses only open data sources. Some APIs enforce rate limits; if you hit limits, try again later.
- For Nominatim, we send a User-Agent header as recommended by the docs.
- Overpass queries are limited to a radius of ~7km and common tourism categories.

## Troubleshooting
- If the UI doesn’t load, ensure the server is running and visit http://127.0.0.1:8000/
- If responses are empty or slow, the external APIs may be rate-limiting or temporarily unavailable.
- If your PowerShell execution policy blocks venv activation, run PowerShell as Administrator and:
  - `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
