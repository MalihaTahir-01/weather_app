import os
from urllib.parse import quote_plus

import requests

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def maps_data(lat: float, lon: float) -> dict:
    return {
        "google_maps_link": f"https://www.google.com/maps/search/?api=1&query={lat},{lon}",
        "embed_url": f"https://maps.google.com/maps?q={lat},{lon}&z=11&output=embed",
    }


def youtube_data(place_name: str) -> dict:
    # "Lahore, Lahore City Tehsil, ..." -> "Lahore"
    short_name = place_name.split(",")[0].strip()
    search_text = f"{short_name} travel"
    fallback_link = (
        f"https://www.youtube.com/results?search_query={quote_plus(search_text)}"
    )

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        return {
            "videos": [],
            "search_link": fallback_link,
            "note": "YOUTUBE_API_KEY not set, showing search link only.",
        }

    try:
        response = requests.get(
            YOUTUBE_SEARCH_URL,
            params={
                "part": "snippet",
                "q": search_text,
                "type": "video",
                "maxResults": 5,
                "safeSearch": "strict",
                "key": api_key,
            },
            timeout=10,
        )
        response.raise_for_status()
        items = response.json().get("items", [])
    except (requests.RequestException, ValueError):
        return {
            "videos": [],
            "search_link": fallback_link,
            "note": "YouTube service unavailable, showing search link only.",
        }

    videos = [
        {
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
        }
        for item in items
    ]
    return {"videos": videos, "search_link": fallback_link}


def get_extras(place_name: str, lat: float, lon: float) -> dict:
    return {"map": maps_data(lat, lon), "youtube": youtube_data(place_name)}