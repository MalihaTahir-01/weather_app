import re
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org"
# Nominatim requires an identifying User-Agent
HEADERS = {
    "User-Agent": "weather-backend-assessment/1.0 (student project)",
    "Accept-Language": "en",
}
# Matches input like "48.8584, 2.2945"
COORD_PATTERN = re.compile(
    r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$"
)


class LocationNotFoundError(Exception):
    """The location doesn't exist or the input is invalid."""


class GeocodingServiceError(Exception):
    """The geocoding service could not be reached."""


def resolve_location(query: str) -> dict:
    query = query.strip()
    if not query:
        raise LocationNotFoundError("Location cannot be empty.")

    match = COORD_PATTERN.match(query)
    if match:
        lat, lon = float(match.group(1)), float(match.group(2))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise LocationNotFoundError(
                "Coordinates out of range (lat -90..90, lon -180..180)."
            )
        return _reverse_lookup(lat, lon)

    return _search(query)


def _search(query: str) -> dict:
    try:
        response = requests.get(
            f"{NOMINATIM_URL}/search",
                        params={
                "q": query,
                "format": "jsonv2",
                "limit": 1,
                "addressdetails": 1,
                "accept-language": "en",
            },
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()
    except requests.RequestException as e:
        raise GeocodingServiceError(f"Geocoding service error: {e}")

    if not results:
        raise LocationNotFoundError(f"Could not find a location for '{query}'.")

    best = results[0]
    return {
        "name": best["display_name"],
        "latitude": float(best["lat"]),
        "longitude": float(best["lon"]),
        "country": best.get("address", {}).get("country"),
    }


def _reverse_lookup(lat: float, lon: float) -> dict:
    try:
        response = requests.get(
            f"{NOMINATIM_URL}/reverse",
                        params={
                "lat": lat,
                "lon": lon,
                "format": "jsonv2",
                "accept-language": "en",
            },
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        raise GeocodingServiceError(f"Geocoding service error: {e}")

    if "error" in data:
        raise LocationNotFoundError(f"No place found at {lat}, {lon}.")

    return {
        "name": data["display_name"],
        "latitude": lat,
        "longitude": lon,
        "country": data.get("address", {}).get("country"),
    }