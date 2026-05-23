from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.core.schemas import CameraSensorState, TrafficLightReading, VehicleProximityReading

logger = logging.getLogger(__name__)

VEHICLE_TYPES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


@dataclass
class StoredReading:
    value: Any
    source: str
    updated_at: datetime


class SensorService:
    """Tashqi svetofor va radar sensor ma'lumotlarini saqlash va birlashtirish."""

    def __init__(self) -> None:
        self._traffic_lights: dict[str, StoredReading] = {}
        self._vehicle_radar: dict[str, StoredReading] = {}

    def _is_stale(self, reading: StoredReading | None) -> bool:
        if reading is None:
            return True
        age = (datetime.now(timezone.utc) - reading.updated_at).total_seconds()
        return age > settings.sensor_stale_after_sec

    def set_traffic_light(self, camera_id: str, signal: str, source: str = "traffic_controller") -> TrafficLightReading:
        normalized = signal.strip().lower()
        if normalized not in {"red", "green", "yellow"}:
            raise ValueError("signal red, green yoki yellow bo'lishi kerak")
        now = datetime.now(timezone.utc)
        self._traffic_lights[camera_id] = StoredReading(normalized, source, now)
        return TrafficLightReading(signal=normalized, source=source, updated_at=now, is_stale=False)

    def set_vehicle_radar(self, camera_id: str, proximity_sec: float, source: str = "radar_sensor") -> VehicleProximityReading:
        now = datetime.now(timezone.utc)
        self._vehicle_radar[camera_id] = StoredReading(float(proximity_sec), source, now)
        return VehicleProximityReading(
            proximity_sec=float(proximity_sec),
            source=source,
            updated_at=now,
            is_stale=False,
        )

    def get_traffic_light_reading(self, camera_id: str) -> TrafficLightReading | None:
        reading = self._traffic_lights.get(camera_id)
        if reading is None:
            return None
        stale = self._is_stale(reading)
        return TrafficLightReading(
            signal=str(reading.value),
            source=reading.source,
            updated_at=reading.updated_at,
            is_stale=stale,
        )

    def get_vehicle_radar_reading(self, camera_id: str) -> VehicleProximityReading | None:
        reading = self._vehicle_radar.get(camera_id)
        if reading is None:
            return None
        stale = self._is_stale(reading)
        return VehicleProximityReading(
            proximity_sec=float(reading.value),
            source=reading.source,
            updated_at=reading.updated_at,
            is_stale=stale,
        )

    def traffic_light_is_red(self, camera_id: str) -> bool:
        reading = self.get_traffic_light_reading(camera_id)
        if reading is None or reading.is_stale:
            return False
        return reading.signal == "red"

    def radar_proximity_sec(self, camera_id: str) -> float | None:
        reading = self.get_vehicle_radar_reading(camera_id)
        if reading is None or reading.is_stale or reading.proximity_sec is None:
            return None
        return reading.proximity_sec

    def merge_vehicle_proximity(
        self,
        camera_id: str,
        vision_proximity_sec: float | None,
    ) -> tuple[float | None, CameraSensorState]:
        radar_sec = self.radar_proximity_sec(camera_id)
        traffic = self.get_traffic_light_reading(camera_id)
        radar_reading = self.get_vehicle_radar_reading(camera_id)

        candidates = [value for value in (radar_sec, vision_proximity_sec) if value is not None]
        merged = min(candidates) if candidates else None

        state = CameraSensorState(
            traffic_light_red=self.traffic_light_is_red(camera_id),
            traffic_light=traffic,
            vehicle_proximity_sec=merged,
            vehicle_proximity=(
                VehicleProximityReading(
                    proximity_sec=merged,
                    source="merged",
                    updated_at=datetime.now(timezone.utc),
                    is_stale=False,
                )
                if merged is not None
                else None
            ),
            vision_vehicle_proximity_sec=vision_proximity_sec,
            radar_vehicle_proximity_sec=radar_sec,
        )
        if radar_reading and not radar_reading.is_stale:
            state.vehicle_proximity = radar_reading
        return merged, state

    async def poll_traffic_light(self, camera_id: str, url: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
                signal = str(payload.get("signal", payload.get("color", ""))).lower()
                if signal:
                    self.set_traffic_light(camera_id, signal, source="traffic_controller_poll")
        except Exception as exc:
            logger.warning("Svetofor poll xato %s: %s", camera_id, exc)

    async def poll_all_traffic_lights(self) -> None:
        for camera_id, url in settings.traffic_light_poll_urls.items():
            await self.poll_traffic_light(camera_id, url)

    def reset_all(self) -> None:
        self._traffic_lights.clear()
        self._vehicle_radar.clear()


sensor_service = SensorService()
