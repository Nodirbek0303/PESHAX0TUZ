from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from app.core.config import settings
from app.core.schemas import FrameResponse
from app.services.alerts import alert_service
from app.services.frame_source import frame_source_manager
from app.services.inference import create_inference_engine
from app.services.sensor_service import sensor_service
from app.services.statistics import statistics_service


class PipelineService:
    """Ma'lumotlar pipeline: kadr → inference → sensor → ogohlantirish."""

    def __init__(self) -> None:
        self.inference = create_inference_engine(settings.inference_mode)
        self._frame_numbers: dict[str, int] = {}
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._broadcast_tasks: dict[str, asyncio.Task] = {}

    def _current_gpu_load(self) -> float:
        status = getattr(self.inference, "status", None)
        if status is not None:
            return status.gpu_load_percent
        return 0.0

    def inference_status(self) -> dict:
        status = getattr(self.inference, "status", None)
        if status is None:
            return {"mode": settings.inference_mode, "ready": False}
        return {
            "mode": status.mode,
            "ready": status.ready,
            "device": status.device,
            "device_name": status.device_name,
            "model_name": status.model_name,
            "tracker": status.tracker,
            "gpu_available": status.gpu_available,
            "gpu_load_percent": status.gpu_load_percent,
            "fallback_active": status.fallback_active,
            "message": status.message,
            "last_error": status.last_error,
        }

    def _next_frame(self, camera_id: str) -> int:
        current = self._frame_numbers.get(camera_id, 0) + 1
        self._frame_numbers[camera_id] = current
        return current

    def process_camera(
        self,
        camera_id: str,
        traffic_light_red: bool | None = None,
        vehicle_proximity_sec: float | None = None,
    ) -> FrameResponse:
        frame_number = self._next_frame(camera_id)
        analysis = self.inference.analyze_frame(camera_id, frame_number)

        merged_proximity, sensor_state = sensor_service.merge_vehicle_proximity(
            camera_id,
            analysis.vision_vehicle_proximity_sec,
        )
        sensor_state.detected_vehicles = len(analysis.vehicles)

        if traffic_light_red is not None:
            traffic_red = traffic_light_red
        else:
            traffic_red = sensor_service.traffic_light_is_red(camera_id)

        if vehicle_proximity_sec is not None:
            final_proximity = vehicle_proximity_sec
        else:
            final_proximity = merged_proximity

        gpu_load = self._current_gpu_load()
        alerts = alert_service.evaluate(
            camera_id=camera_id,
            persons=analysis.persons,
            traffic_light_red=traffic_red,
            vehicle_proximity_sec=final_proximity,
            gpu_load=gpu_load,
        )

        violation_count = sum(1 for alert in alerts if alert.severity.value == "RED")
        latest = frame_source_manager.get_latest_frame(camera_id)
        frame_width = latest.shape[1] if latest is not None else 1280
        frame_height = latest.shape[0] if latest is not None else 720

        statistics = statistics_service.compute_statistics(
            camera_id,
            analysis.persons,
            violation_delta=violation_count,
            frame_width=frame_width,
        )
        zone_counts = statistics_service.compute_zone_counts(analysis.persons, frame_width=frame_width)

        return FrameResponse(
            timestamp=datetime.now(timezone.utc),
            camera_id=camera_id,
            frame_number=frame_number,
            frame_width=frame_width,
            frame_height=frame_height,
            snapshot_url=f"{settings.api_prefix}/snapshot/{camera_id}",
            detected_persons=analysis.persons,
            detected_vehicles=analysis.vehicles,
            sensor_state=sensor_state,
            statistics=statistics,
            active_alerts=alerts,
            zone_counts=zone_counts,
        )

    async def subscribe(self, camera_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=5)
        self._subscribers.setdefault(camera_id, set()).add(queue)
        if camera_id not in self._broadcast_tasks or self._broadcast_tasks[camera_id].done():
            self._broadcast_tasks[camera_id] = asyncio.create_task(self.broadcast_loop(camera_id))
        return queue

    def unsubscribe(self, camera_id: str, queue: asyncio.Queue) -> None:
        subscribers = self._subscribers.get(camera_id)
        if subscribers and queue in subscribers:
            subscribers.remove(queue)
        if subscribers is not None and len(subscribers) == 0:
            task = self._broadcast_tasks.pop(camera_id, None)
            if task and not task.done():
                task.cancel()

    async def broadcast_loop(self, camera_id: str) -> None:
        interval = settings.ws_update_interval_ms / 1000
        while True:
            frame = self.process_camera(camera_id)
            subscribers = list(self._subscribers.get(camera_id, set()))
            for queue in subscribers:
                if queue.full():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                await queue.put(frame)
            await asyncio.sleep(interval)


pipeline_service = PipelineService()
