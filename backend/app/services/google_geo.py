from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def reverse_geocode(lat: float, lon: float) -> dict | None:
    if not settings.google_api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "latlng": f"{lat},{lon}",
                    "key": settings.google_api_key,
                    "language": "uz",
                },
            )
            response.raise_for_status()
            payload = response.json()
    except Exception as exc:
        logger.warning("Google Geocoding xato: %s", exc)
        return None

    if payload.get("status") != "OK" or not payload.get("results"):
        logger.warning("Google Geocoding javob: %s", payload.get("status"))
        return None

    top = payload["results"][0]
    return {
        "formatted_address": top.get("formatted_address"),
        "place_id": top.get("place_id"),
        "location_type": top.get("geometry", {}).get("location_type"),
        "provider": "google_maps",
    }
