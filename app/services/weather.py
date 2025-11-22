from typing import Optional
import datetime as dt
import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


async def get_weather_summary(lat: float, lon: float, display_name: str) -> Optional[str]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": ["precipitation_probability"],
        "timezone": "auto",
    }
    timeout = httpx.Timeout(10.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(OPEN_METEO_URL, params=params)
        if resp.status_code != 200:
            return None
        data = resp.json()

    try:
        current = data.get("current_weather", {})
        temp_c = current.get("temperature")
        # Find precip prob for current hour if available
        precip_prob = None
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        probs = hourly.get("precipitation_probability", [])
        if times and probs:
            # Match current hour by string prefix up to hour
            now = dt.datetime.now(dt.timezone.utc)
            # Data is in local timezone (timezone="auto"), so fall back to last item if matching fails
            target_index = None
            # Try to find the closest time index (exact match first)
            now_str_prefix = now.strftime("%Y-%m-%dT%H")
            for i, t in enumerate(times):
                if t.startswith(now_str_prefix):
                    target_index = i
                    break
            if target_index is None:
                # fallback to the last available probability value
                target_index = max(len(probs) - 1, 0)
            precip_prob = probs[target_index]

        city = display_name.split(",")[0]
        if temp_c is not None and precip_prob is not None:
            return f"In {city} it’s currently {round(temp_c)}°C with a chance of {round(precip_prob)}% to rain."
        if temp_c is not None:
            return f"In {city} it’s currently {round(temp_c)}°C."
        return None
    except Exception:
        return None
