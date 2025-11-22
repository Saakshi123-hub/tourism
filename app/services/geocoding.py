from pydantic import BaseModel
from typing import Optional
import httpx
import re

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Per Nominatim policy, include a descriptive UA with a contact URL.
# Replace the URL below with your project URL if available.
USER_AGENT = "multi-agent-tourism/1.0 (+https://openstreetmap.org)"
OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


class GeoResult(BaseModel):
    display_name: str
    lat: float
    lon: float


async def geocode_place(place: str) -> Optional[GeoResult]:
    # Build a small set of candidate queries to be robust to noisy input
    def candidates(p: str) -> list[str]:
        cands: list[str] = []
        s = p.strip()
        if s:
            cands.append(s)
        # If there are commas, try the last segment (often the city)
        parts = [seg.strip() for seg in s.split(',') if seg.strip()]
        if parts:
            cands.append(parts[-1])
        # Keep only letters, spaces and common punctuations
        simple = re.sub(r"[^A-Za-z\s\-\.'’]", " ", s)
        simple = re.sub(r"\s+", " ", simple).strip()
        if simple and simple.lower() != s.lower():
            cands.append(simple)
        # Capitalized words run (e.g., "New York", "San Francisco")
        caps = " ".join(w for w in re.findall(r"[A-Z][a-zA-Z'’\-]*", s))
        if caps:
            cands.append(caps)
        # Deduplicate while preserving order
        seen = set()
        uniq = []
        for q in cands:
            k = q.lower()
            if k not in seen and len(q) >= 2:
                uniq.append(q)
                seen.add(k)
        return uniq[:4]

    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en",
        "Accept": "application/json",
        "Referer": "https://openstreetmap.org",
    }
    timeout = httpx.Timeout(10.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        for q in candidates(place):
            params = {
                "q": q,
                "format": "jsonv2",
                "limit": 3,
                "addressdetails": 0,
            }
            resp = await client.get(NOMINATIM_URL, params=params)
            if resp.status_code != 200:
                continue
            data = resp.json()
            if not data:
                continue
            # Prefer city/town/village results if present
            chosen = None
            for item in data:
                cls = item.get("class") or item.get("type") or ""
                if str(cls).lower() in {"place", "boundary"}:
                    chosen = item
                    break
            if not chosen:
                chosen = data[0]
            try:
                return GeoResult(
                    display_name=chosen.get("display_name", q),
                    lat=float(chosen["lat"]),
                    lon=float(chosen["lon"]),
                )
            except Exception:
                continue
    # Fallback: Open‑Meteo Geocoding (open source) if Nominatim had no match
    try:
        async with httpx.AsyncClient(timeout=timeout, headers={"User-Agent": USER_AGENT}) as client:
            resp = await client.get(OPEN_METEO_GEOCODE_URL, params={"name": place, "count": 1, "language": "en"})
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results") or []
                if results:
                    r = results[0]
                    name_parts = [p for p in [r.get("name"), r.get("admin1"), r.get("country") ] if p]
                    display = ", ".join(name_parts) or place
                    return GeoResult(display_name=display, lat=float(r["latitude"]), lon=float(r["longitude"]))
    except Exception:
        pass
    return None
