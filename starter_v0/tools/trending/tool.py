from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err


# Common WOEID locations for reference
WOEID_NAMES: dict[int, str] = {
    1: "Worldwide",
    23424840: "Vietnam",
    23424977: "United States",
    44418: "London",
    1132599: "Tokyo",
    23424856: "Japan",
    23424848: "Indonesia",
    615702: "Paris",
    638242: "Berlin",
    2459115: "New York",
    2487956: "San Francisco",
}


def _twitter_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    key = os.getenv("RAPIDAPI_KEY")
    host = os.getenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")
    if not key:
        raise RuntimeError("Missing RAPIDAPI_KEY env var")
    response = requests.get(
        f"https://{host}{path}",
        params=params,
        headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def get_trending(
    woeid: int = 1,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Lấy trending topics trên Twitter/X tại một địa điểm.

    Args:
        woeid: Yahoo Where On Earth ID. 1=Worldwide, 23424840=Vietnam,
               23424977=USA, 1132599=Tokyo.
        limit: Số lượng trending topics trả về (1-25, mặc định 10).

    Returns:
        dict với location name và items (name, tweet_volume, url).
    """
    try:
        woeid = int(woeid or 1)
        limit = max(1, min(int(limit or 10), 25))
        location_name = WOEID_NAMES.get(woeid, f"Location {woeid}")

        data = _twitter_get("/trends/available.php" if woeid == 0 else "/trends.php", {"woeid": woeid})

        # Handle different response shapes from the API
        trends_raw: list[dict[str, Any]] = []
        if isinstance(data, list):
            # Direct list of trends
            trends_raw = data
        elif isinstance(data, dict):
            # Nested: [{trends: [...]}] or {trends: [...]}
            if "trends" in data:
                trends_raw = data["trends"]
            else:
                # Try first element if list-like structure
                for key in data:
                    val = data[key]
                    if isinstance(val, list):
                        trends_raw = val
                        break

        items = []
        for trend in trends_raw[:limit]:
            name = trend.get("name") or trend.get("query") or ""
            tweet_vol = trend.get("tweet_volume") or trend.get("tweetVolume")
            url = trend.get("url") or (
                f"https://twitter.com/search?q={name.replace(' ', '%20')}" if name else ""
            )
            if name:
                items.append({
                    "name": name,
                    "tweet_volume": tweet_vol,
                    "url": url,
                    "source": "twitter.com",
                })

        return {
            "tool": "trending",
            "woeid": woeid,
            "location": location_name,
            "items": items,
            "total_returned": len(items),
        }
    except Exception as exc:
        return err("trending", exc)
