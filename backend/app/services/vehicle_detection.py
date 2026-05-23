from __future__ import annotations

import math
from dataclasses import dataclass

from app.core.config import settings
from app.core.schemas import DetectedPerson, DetectedVehicle
from app.services.attributes import point_in_polygon


YOLO_VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}


@dataclass
class VehicleTrack:
    vehicle_id: str
    vehicle_type: str
    bbox: list[float]
    confidence: float
    path: list[tuple[float, float, float]]


def _bbox_center(bbox: list[float]) -> tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)


def _bbox_bottom_center(bbox: list[float]) -> tuple[float, float]:
    return ((bbox[0] + bbox[2]) / 2, bbox[3])


def _speed_px_per_sec(path: list[tuple[float, float, float]]) -> float:
    if len(path) < 2:
        return 0.0
    x1, y1, t1 = path[0]
    x2, y2, t2 = path[-1]
    dt = max(t2 - t1, 1e-3)
    return math.hypot(x2 - x1, y2 - y1) / dt


def _crosswalk_top_y(polygons: list[list[list[float]]]) -> float | None:
    if not polygons:
        return None
    return min(point[1] for polygon in polygons for point in polygon)


def vehicle_approaching_crosswalk(
    bbox: list[float],
    polygons: list[list[list[float]]],
    buffer_px: int,
) -> bool:
    if not polygons:
        return False
    foot_x, foot_y = _bbox_bottom_center(bbox)
    top_y = _crosswalk_top_y(polygons)
    if top_y is None:
        return False
    if foot_y < top_y - buffer_px:
        return False
    for polygon in polygons:
        min_x = min(point[0] for point in polygon)
        max_x = max(point[0] for point in polygon)
        if min_x - buffer_px <= foot_x <= max_x + buffer_px:
            return True
        if point_in_polygon(foot_x, foot_y, polygon):
            return True
    return False


def update_vehicle_tracks(
    camera_tracks: dict[str, VehicleTrack],
    detections: list[tuple[list[float], float, str]],
    now_ts: float,
) -> list[VehicleTrack]:
    matched: set[str] = set()
    active: list[VehicleTrack] = []

    for bbox, confidence, vehicle_type in detections:
        center = _bbox_center(bbox)
        best_id: str | None = None
        best_dist = 80.0
        for track_id, track in camera_tracks.items():
            if track.vehicle_type != vehicle_type:
                continue
            last_x, last_y, _ = track.path[-1]
            dist = math.hypot(center[0] - last_x, center[1] - last_y)
            if dist < best_dist:
                best_dist = dist
                best_id = track_id

        if best_id is None:
            best_id = f"V-{len(camera_tracks) + 1:04d}"
            camera_tracks[best_id] = VehicleTrack(
                vehicle_id=best_id,
                vehicle_type=vehicle_type,
                bbox=bbox,
                confidence=confidence,
                path=[],
            )

        track = camera_tracks[best_id]
        track.bbox = bbox
        track.confidence = confidence
        track.path.append((center[0], bbox[3], now_ts))
        track.path = track.path[-20:]
        matched.add(best_id)
        active.append(track)

    stale_ids = [track_id for track_id in camera_tracks if track_id not in matched]
    for track_id in stale_ids:
        camera_tracks.pop(track_id, None)
    return active


def build_detected_vehicles(
    tracks: list[VehicleTrack],
    polygons: list[list[list[float]]],
) -> list[DetectedVehicle]:
    vehicles: list[DetectedVehicle] = []
    for track in tracks:
        speed_px = _speed_px_per_sec(track.path)
        speed_ms = round(speed_px / 120.0, 2)
        approaching = vehicle_approaching_crosswalk(
            track.bbox,
            polygons,
            settings.vehicle_approach_buffer_px,
        )
        vehicles.append(
            DetectedVehicle(
                vehicle_id=track.vehicle_id,
                vehicle_type=track.vehicle_type,
                bbox=[round(v, 1) for v in track.bbox],
                confidence=round(track.confidence, 3),
                speed_ms=speed_ms,
                approaching_crosswalk=approaching,
            )
        )
    return vehicles


def compute_vision_vehicle_proximity(
    vehicles: list[DetectedVehicle],
    persons: list[DetectedPerson],
    vehicle_tracks: list[VehicleTrack],
) -> float | None:
    crosswalk_persons = [person for person in persons if person.in_crosswalk]
    if not crosswalk_persons:
        return None

    min_sec: float | None = None
    track_by_id = {track.vehicle_id: track for track in vehicle_tracks}

    for vehicle in vehicles:
        if not vehicle.approaching_crosswalk:
            continue
        track = track_by_id.get(vehicle.vehicle_id)
        if track is None:
            continue
        speed_px = _speed_px_per_sec(track.path)
        if speed_px < 8.0:
            continue

        vx, vy = _bbox_bottom_center(vehicle.bbox)
        for person in crosswalk_persons:
            px, py = _bbox_bottom_center(person.bbox)
            distance_px = math.hypot(px - vx, py - vy)
            sec = distance_px / speed_px
            if sec <= settings.vehicle_proximity_alert_sec * 3:
                min_sec = sec if min_sec is None else min(min_sec, sec)

    return round(min_sec, 2) if min_sec is not None else None
