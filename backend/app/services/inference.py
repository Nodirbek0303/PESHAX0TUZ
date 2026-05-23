from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from app.core.config import settings
from app.core.schemas import (
    AgeRange,
    CrosswalkPresence,
    DetectedPerson,
    DetectedVehicle,
    Gender,
    GroupStatus,
    HandOccupancy,
    PersonCategory,
    SpeedClass,
    TrackPoint,
)
from app.services.attributes import (
    bbox_overlap_ratio,
    compute_crossing_time,
    crosswalk_presence,
    dominant_clothing_color,
    estimate_direction,
    estimate_group_status,
    estimate_speed_ms,
    point_in_polygon,
    scale_polygon,
)
from app.services.camera_manager import camera_manager
from app.services.frame_source import frame_source_manager
from app.services.gpu_monitor import get_gpu_status, resolve_device
from app.services.vehicle_detection import (
    YOLO_VEHICLE_CLASSES,
    build_detected_vehicles,
    compute_vision_vehicle_proximity,
    update_vehicle_tracks,
)

logger = logging.getLogger(__name__)

PERSON_CLASS = 0
DETECTION_CLASSES = [0, 2, 3, 5, 7]


@dataclass
class FrameAnalysis:
    persons: list[DetectedPerson]
    vehicles: list[DetectedVehicle]
    vision_vehicle_proximity_sec: float | None


@dataclass
class InferenceEngineStatus:
    mode: str
    ready: bool
    device: str
    device_name: str | None
    model_name: str
    tracker: str
    gpu_available: bool
    gpu_load_percent: float
    fallback_active: bool
    message: str
    last_error: str | None = None


class GpuInferenceEngine:
    """YOLOv8 + DeepSORT — piyoda va transport kameradan."""

    mode = "gpu"

    def __init__(self) -> None:
        self._model = None
        self._tracker = None
        self._ready = False
        self._device = resolve_device(settings.inference_device)
        self._track_state: dict[str, dict[int, dict]] = {}
        self._vehicle_tracks: dict[str, dict] = {}
        self._last_error: str | None = None

    @property
    def status(self) -> InferenceEngineStatus:
        gpu = get_gpu_status(self._device)
        return InferenceEngineStatus(
            mode="gpu",
            ready=self._ready,
            device=self._device,
            device_name=gpu.device_name,
            model_name=settings.yolo_model,
            tracker="DeepSORT",
            gpu_available=gpu.available,
            gpu_load_percent=gpu.load_percent,
            fallback_active=False,
            message=(
                "Kamera deteksiyasi faol (piyoda + transport)"
                if self._ready
                else "Inference yuklanmadi — kadr tahlili mavjud emas"
            ),
            last_error=self._last_error,
        )

    def load(self) -> bool:
        try:
            from deep_sort_realtime.deepsort_tracker import DeepSort
            from ultralytics import YOLO

            self._device = resolve_device(settings.inference_device)
            self._model = YOLO(settings.yolo_model)
            self._model.to(self._device)
            self._tracker = DeepSort(
                max_age=settings.tracker_max_age,
                n_init=settings.tracker_n_init,
                embedder="mobilenet",
                half=self._device.startswith("cuda"),
            )

            warmup_frame = np.zeros((640, 640, 3), dtype=np.uint8)
            self._model.predict(
                warmup_frame,
                conf=settings.yolo_confidence,
                classes=DETECTION_CLASSES,
                verbose=False,
                device=self._device,
            )
            self._ready = True
            self._last_error = None
            logger.info("Inference yuklandi: model=%s device=%s", settings.yolo_model, self._device)
            return True
        except Exception as exc:
            self._ready = False
            self._last_error = str(exc)
            logger.exception("Inference yuklanmadi: %s", exc)
            return False

    def _get_crosswalk_polygons(self, camera_id: str, frame_w: int, frame_h: int) -> list[list[list[float]]]:
        camera = camera_manager.get_camera(camera_id)
        if not camera:
            return []
        ref_w, ref_h = settings.reference_frame_width, settings.reference_frame_height
        return [
            scale_polygon(zone.polygon, ref_w, ref_h, frame_w, frame_h)
            for zone in camera.crosswalk_zones
        ]

    def _person_in_crosswalk(
        self,
        bbox: list[float],
        polygons: list[list[list[float]]],
        frame_w: int,
        frame_h: int,
    ) -> tuple[bool, float]:
        foot_x = (bbox[0] + bbox[2]) / 2
        foot_y = bbox[3]
        overlap = 0.0
        inside = False
        for polygon in polygons:
            overlap = max(overlap, bbox_overlap_ratio(bbox, polygon, frame_w, frame_h))
            if point_in_polygon(foot_x, foot_y, polygon):
                inside = True
        return inside, overlap

    def analyze_frame(self, camera_id: str, frame_number: int | None = None) -> FrameAnalysis:
        if not self._ready:
            return FrameAnalysis(persons=[], vehicles=[], vision_vehicle_proximity_sec=None)

        frame, _meta = frame_source_manager.get_frame(camera_id)
        if frame is None:
            return FrameAnalysis(persons=[], vehicles=[], vision_vehicle_proximity_sec=None)

        frame_h, frame_w = frame.shape[:2]
        results = self._model.predict(
            frame,
            conf=settings.yolo_confidence,
            iou=settings.yolo_iou,
            classes=DETECTION_CLASSES if settings.enable_vision_vehicle_detection else [PERSON_CLASS],
            verbose=False,
            device=self._device,
        )

        person_detections = []
        vehicle_detections: list[tuple[list[float], float, str]] = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                if cls_id == PERSON_CLASS:
                    person_detections.append(([x1, y1, x2 - x1, y2 - y1], confidence, "person"))
                elif settings.enable_vision_vehicle_detection and cls_id in YOLO_VEHICLE_CLASSES:
                    vehicle_detections.append(
                        ([x1, y1, x2, y2], confidence, YOLO_VEHICLE_CLASSES[cls_id])
                    )

        tracks = self._tracker.update_tracks(person_detections, frame=frame)
        polygons = self._get_crosswalk_polygons(camera_id, frame_w, frame_h)
        camera_tracks = self._track_state.setdefault(camera_id, {})
        now = datetime.now(timezone.utc)
        now_ts = now.timestamp()
        persons: list[DetectedPerson] = []
        active_centers: list[tuple[float, float]] = []

        for track in tracks:
            if not track.is_confirmed() or track.det_conf is None:
                continue

            track_id = track.track_id
            left, top, width, height = track.to_ltrb()
            bbox = [float(left), float(top), float(left + width), float(top + height)]
            center = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
            active_centers.append(center)

            state = camera_tracks.setdefault(track_id, {"path": [], "crosswalk_history": [], "first_seen": now})
            state["path"].append(TrackPoint(x=center[0], y=bbox[3], t=now_ts))
            state["path"] = state["path"][-30:]

            in_crosswalk, overlap = self._person_in_crosswalk(bbox, polygons, frame_w, frame_h)
            state["crosswalk_history"].append(in_crosswalk)
            state["crosswalk_history"] = state["crosswalk_history"][-30:]

            path = state["path"]
            speed_ms, speed_class = estimate_speed_ms(path)
            direction = estimate_direction(path)
            clothing = dominant_clothing_color(frame, bbox)
            peshaxot = crosswalk_presence(in_crosswalk, overlap)
            crossing_time = compute_crossing_time(path, state["crosswalk_history"])

            persons.append(
                DetectedPerson(
                    person_id=f"P-{str(track_id).replace('-', '')[:8].upper()}",
                    category=PersonCategory.PIYODA,
                    gender=Gender.ANIQLANMADI,
                    age_range=AgeRange.ANIQLANMADI,
                    clothing_color=clothing,
                    direction=direction,
                    speed_ms=speed_ms,
                    speed_class=speed_class,
                    group_status=GroupStatus.YOLGIZ,
                    qol_band=HandOccupancy.BOSH,
                    yol_qaraydi=False,
                    peshaxot_ichida=peshaxot,
                    in_crosswalk=in_crosswalk,
                    bbox=[round(value, 1) for value in bbox],
                    confidence=round(float(track.det_conf), 3),
                    track_path=path[-10:],
                    birinchi_korish=state["first_seen"],
                    oxirgi_korish=now,
                    otish_vaqti=crossing_time,
                )
            )

        for person, center in zip(persons, active_centers):
            nearby = sum(
                1
                for other in active_centers
                if math.hypot(other[0] - center[0], other[1] - center[1]) < 120
            )
            person.group_status = estimate_group_status(nearby)

        vehicle_track_map = self._vehicle_tracks.setdefault(camera_id, {})
        active_vehicle_tracks = update_vehicle_tracks(vehicle_track_map, vehicle_detections, now_ts)
        vehicles = build_detected_vehicles(active_vehicle_tracks, polygons)
        vision_proximity = None
        if settings.enable_vision_vehicle_detection:
            vision_proximity = compute_vision_vehicle_proximity(vehicles, persons, active_vehicle_tracks)

        return FrameAnalysis(
            persons=persons,
            vehicles=vehicles,
            vision_vehicle_proximity_sec=vision_proximity,
        )

    def process_frame(self, camera_id: str, frame_number: int | None = None) -> list[DetectedPerson]:
        return self.analyze_frame(camera_id, frame_number).persons

    def shutdown(self) -> None:
        frame_source_manager.release()


def create_inference_engine(_mode: str) -> GpuInferenceEngine:
    engine = GpuInferenceEngine()
    engine.load()
    return engine
