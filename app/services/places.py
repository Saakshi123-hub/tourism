from typing import List
import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

CATEGORIES = "attraction|museum|zoo|gallery|theme_park|viewpoint|park|castle|palace|aquarium|monument|artwork"


async def get_top_places(lat: float, lon: float, limit: int = 5) -> List[str]:
    # Overpass QL query: search for notable tourism features within ~7km radius
    radius_m = 7000
    query = f"""
    [out:json][timeout:25];
    (
      node(around:{radius_m},{lat},{lon})["tourism"~"{CATEGORIES}"];
      way(around:{radius_m},{lat},{lon})["tourism"~"{CATEGORIES}"];
      relation(around:{radius_m},{lat},{lon})["tourism"~"{CATEGORIES}"];
    );
    out tags center {max(50, limit*5)};
    """
    timeout = httpx.Timeout(20.0, connect=10.0)
    headers = {"User-Agent": "multi-agent-tourism-app/1.0 (contact: example@example.com)"}
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        resp = await client.post(OVERPASS_URL, data={"data": query})
        if resp.status_code != 200:
            return []
        data = resp.json()

    elements = data.get("elements", [])
    names = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            # Try localized name fallback
            name = next((v for k, v in tags.items() if k.startswith("name:")), None)
        if name and name.lower() not in seen:
            names.append(name)
            seen.add(name.lower())
        if len(names) >= limit:
            break
    return names
