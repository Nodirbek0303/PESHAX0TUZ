from __future__ import annotations

import math

import cv2
import numpy as np

from app.core.schemas import (
    CrosswalkPresence,
    Direction,
    GroupStatus,
    SpeedClass,
    TrackPoint,
)


COLOR_NAMES = [
    ("qora", (26, 26, 26)),
    ("oq", (245, 245, 245)),
    ("ko'k", (37, 99, 235)),
    ("qizil", (220, 38, 38)),
    ("yashil", (22, 163, 74)),
    ("kulrang", (107, 114, 128)),
    ("sariq", (234, 179, 8)),
]


def point_in_polygon(x: float, y: float, polygon: list[list[float]]) -> bool:
    inside = False
    count = len(polygon)
    for i in range(count):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % count]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1):
            inside = not inside
    return inside


def scale_polygon(polygon: list[list[float]], src_w: int, src_h: int, dst_w: int, dst_h: int) -> list[list[float]]:
    scale_x = dst_w / max(src_w, 1)
    scale_y = dst_h / max(src_h, 1)
    return [[point[0] * scale_x, point[1] * scale_y] for point in polygon]


def dominant_clothing_color(frame: np.ndarray, bbox: list[float]) -> str:
    x1, y1, x2, y2 = [int(v) for v in bbox]
    h, w = frame.shape[:2]
    x1, y2 = max(0, x1), min(h, y2)
    x2, y1 = min(w, x2), max(0, y1)
    if x2 <= x1 or y2 <= y1:
        return "aniqlanmadi"

    crop = frame[y1:y2, x1:x2]
    if crop.size == 0:
        return "aniqlanmadi"

    torso = crop[int(crop.shape[0] * 0.25) : int(crop.shape[0] * 0.65)]
    if torso.size == 0:
        torso = crop
    mean_bgr = torso.reshape(-1, 3).mean(axis=0)
    best_name = "kulrang"
    best_dist = float("inf")
    for name, rgb in COLOR_NAMES:
        bgr = np.array([rgb[2], rgb[1], rgb[0]], dtype=np.float32)
        dist = float(np.linalg.norm(mean_bgr - bgr))
        if dist < best_dist:
            best_dist = dist
            best_name = name
    hex_color = "#%02x%02x%02x" % tuple(int(v) for v in mean_bgr[::-1])
    return f"{best_name} ({hex_color})"


def estimate_direction(path: list[TrackPoint]) -> Direction:
    if len(path) < 2:
        return Direction.N
    start = path[-2]
    end = path[-1]
    dx = end.x - start.x
    dy = end.y - start.y
    angle = math.degrees(math.atan2(-dy, dx)) % 360
    directions = [
        (Direction.E, 0),
        (Direction.SE, 45),
        (Direction.S, 90),
        (Direction.SW, 135),
        (Direction.W, 180),
        (Direction.NW, 225),
        (Direction.N, 270),
        (Direction.NE, 315),
    ]
    best = Direction.N
    best_delta = 999.0
    for direction, center in directions:
        delta = min(abs(angle - center), 360 - abs(angle - center))
        if delta < best_delta:
            best_delta = delta
            best = direction
    return best


def estimate_speed_ms(path: list[TrackPoint], pixels_per_meter: float = 120.0) -> tuple[float, SpeedClass]:
    if len(path) < 2:
        return 0.0, SpeedClass.SEKIN
    start = path[0]
    end = path[-1]
    dt = max(end.t - start.t, 1e-3)
    distance_px = math.hypot(end.x - start.x, end.y - start.y)
    speed = distance_px / pixels_per_meter / dt
    if speed < 0.8:
        return round(speed, 2), SpeedClass.SEKIN
    if speed <= 1.5:
        return round(speed, 2), SpeedClass.NORMAL
    return round(speed, 2), SpeedClass.TEZ


def estimate_group_status(track_count_nearby: int) -> GroupStatus:
    if track_count_nearby >= 6:
        return GroupStatus.OLOMON_6_PLUS
    if track_count_nearby >= 3:
        return GroupStatus.GURUH_3_5
    if track_count_nearby == 2:
        return GroupStatus.JUFT
    return GroupStatus.YOLGIZ


def crosswalk_presence(in_crosswalk: bool, overlap_ratio: float) -> CrosswalkPresence:
    if in_crosswalk and overlap_ratio > 0.65:
        return CrosswalkPresence.HA
    if overlap_ratio > 0.2:
        return CrosswalkPresence.QISMAN
    return CrosswalkPresence.YOQ


def bbox_overlap_ratio(
    bbox: list[float],
    polygon: list[list[float]],
    frame_w: int = 1280,
    frame_h: int = 720,
) -> float:
    x1, y1, x2, y2 = [int(v) for v in bbox]
    mask = np.zeros((frame_h, frame_w), dtype=np.uint8)
    pts = np.array(polygon, dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)
    region = mask[max(0, y1) : y2, max(0, x1) : x2]
    if region.size == 0:
        return 0.0
    return float(np.count_nonzero(region)) / float(region.size)


def compute_crossing_time(path: list[TrackPoint], in_crosswalk_history: list[bool]) -> float | None:
    if sum(in_crosswalk_history) < 3 or len(path) < 2:
        return None
    start = path[0].t
    end = path[-1].t
    return round(max(end - start, 0.0), 1)
