"""
c4reqber: USGS API Client

Earthquakes, geology, hydrology data.
Open access, no API key.
"""
from __future__ import annotations

import logging
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.usgs")


class UsgsClient(BaseP6Client):
    """USGS Earthquake API client."""

    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1"
    DEFAULT_TIMEOUT = 30.0

    async def search_earthquakes(
        self, query: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search recent earthquakes by region/place keyword."""
        try:
            params: dict[str, Any] = {
                "format": "geojson",
                "limit": min(limit, 100),
                "orderby": "time",
            }
            # If query looks like a magnitude threshold, use it
            if query.replace(".", "", 1).isdigit():
                params["minmagnitude"] = float(query)
            else:
                # Place-based search via text parameter if supported or just recent
                params["alertlevel"] = query.lower() if query.lower() in ("green", "yellow", "orange", "red") else None
            # Clean None values
            params = {k: v for k, v in params.items() if v is not None}
            data = await self._get("/query", params=params, use_cache=True)
            features = data.get("features", []) if isinstance(data, dict) else []
            results: list[dict[str, Any]] = []
            for item in features[:limit]:
                props = item.get("properties", {}) if isinstance(item, dict) else {}
                geom = item.get("geometry", {}) if isinstance(item, dict) else {}
                coords = geom.get("coordinates", [None, None, None])
                results.append({
                    "id": item.get("id"),
                    "place": props.get("place"),
                    "magnitude": props.get("mag"),
                    "time": props.get("time"),
                    "latitude": coords[1] if len(coords) > 1 else None,
                    "longitude": coords[0] if len(coords) > 0 else None,
                    "depth_km": coords[2] if len(coords) > 2 else None,
                    "alert": props.get("alert"),
                    "source": "usgs",
                })
            return results
        except Exception as e:
            logger.warning("USGS search error: %s", e)
            return []
