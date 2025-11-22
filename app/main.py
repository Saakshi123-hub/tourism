from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re
from typing import Optional

from app.services.geocoding import geocode_place
from app.services.weather import get_weather_summary
from app.services.places import get_top_places

app = FastAPI(title="Multi-Agent Tourism System")

# Serve static UI
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    text: str


class QueryResponse(BaseModel):
    place: Optional[str] = None
    weather_summary: Optional[str] = None
    places: Optional[list[str]] = None
    message: str


WEATHER_KEYWORDS = [
    "weather",
    "temperature",
    "rain",
    "forecast",
    "hot",
    "cold",
]
PLACES_KEYWORDS = [
    "places",
    "attractions",
    "visit",
    "see",
    "go",
    "plan",
    "trip",
]


def extract_place(user_text: str) -> Optional[str]:
    text = user_text.strip()
    # Try to find phrases like "to <place>", "in <place>"
    patterns = [
        r"(?:to|in|at)\s+([A-Za-z\s\-\.'’]+?)(?:\?|\.|,|$)",
        r"going to\s+([A-Za-z\s\-\.'’]+?)(?:\?|\.|,|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Avoid generic trailing words
            candidate = re.sub(r"\b(what|is|the|there|and|but)\b.*$", "", candidate, flags=re.IGNORECASE).strip()
            if candidate:
                return candidate
    # Fallback: if user text is short, assume it's the place
    if len(text.split()) <= 4:
        return text
    return None


def infer_intents(user_text: str) -> tuple[bool, bool]:
    t = user_text.lower()
    ask_weather = any(k in t for k in WEATHER_KEYWORDS)
    ask_places = any(k in t for k in PLACES_KEYWORDS)
    if not (ask_weather or ask_places):
        # default to both if user says plan my trip or gives only place
        if re.search(r"plan|itinerary|trip", t) or extract_place(user_text):
            ask_weather = True
            ask_places = True
    return ask_weather, ask_places


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    ask_weather, ask_places = infer_intents(req.text)
    place_query = extract_place(req.text) or req.text.strip()

    # Geo lookup (child/tool: Nominatim)
    geo = await geocode_place(place_query)
    if not geo:
        return QueryResponse(message="It doesn’t know this place exist. Please check the place name.")

    display_name = geo.display_name
    lat, lon = geo.lat, geo.lon

    weather_summary = None
    places_list: Optional[list[str]] = None

    # Weather agent (child/tool: Open-Meteo)
    if ask_weather:
        weather_summary = await get_weather_summary(lat, lon, display_name)

    # Places agent (child/tool: Overpass via OSM)
    if ask_places:
        places_list = await get_top_places(lat, lon, limit=5)

    # Compose message
    parts = []
    if ask_weather and weather_summary:
        parts.append(weather_summary)
    if ask_places and places_list:
        places_text = "\n".join(places_list)
        parts.append(f"And these are the places you can go:\n{places_text}" if ask_weather else f"In {display_name.split(',')[0]} these are the places you can go,\n{places_text}")

    if not parts:
        parts.append(f"What would you like to know about {display_name.split(',')[0]}? You can ask for weather or attractions.")

    return QueryResponse(
        place=display_name,
        weather_summary=weather_summary,
        places=places_list,
        message=" ".join(parts),
    )
