"""
c4reqber: NOAA Climate Data Online Client

Access to weather stations, daily summaries, GHCN data.
License: Free API key required
"""
from __future__ import annotations

import logging
import os
from typing import Any

from .base_p6 import BaseP6Client


logger = logging.getLogger("c4reqber.knowledge.noaa")


class NOAAClient(BaseP6Client):
    """NOAA Climate Data Online (CDO) API client."""

    BASE_URL = "https://www.ncdc.noaa.gov/cdo-web/api/v2"

    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key or os.getenv("NOAA_API_KEY", "")
        headers = {"token": self.api_key} if self.api_key else {}
        super().__init__(headers=headers)

    async def search_stations(
        self,
        location: str = "",
        dataset: str = "GHCND",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search weather stations."""
        if not self.api_key:
            logger.warning("NOAA_API_KEY not set")
            return []
        params: dict[str, Any] = {"datasetid": dataset, "limit": limit}
        if location:
            params["locationid"] = location
        try:
            data = await self._get("/stations", params=params)
            return data.get("results", [])
        except Exception as e:
            logger.warning("NOAA stations error: %s", e)
            return []

    async def get_daily_data(
        self,
        station_id: str,
        start_date: str,
        end_date: str,
        dataset: str = "GHCND",
    ) -> list[dict[str, Any]]:
        """Fetch daily climate data for a station."""
        if not self.api_key:
            return []
        try:
            data = await self._get("/data", params={
                "datasetid": dataset,
                "stationid": station_id,
                "startdate": start_date,
                "enddate": end_date,
                "limit": 1000,
            })
            return data.get("results", [])
        except Exception as e:
            logger.warning("NOAA daily data error: %s", e)
            return []

    async def get_datasets(self) -> list[dict[str, Any]]:
        """List available datasets."""
        if not self.api_key:
            return []
        try:
            data = await self._get("/datasets")
            return data.get("results", [])
        except Exception as e:
            logger.warning("NOAA datasets error: %s", e)
            return []
