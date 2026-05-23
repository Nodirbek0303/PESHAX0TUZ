from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from app.core.config import settings
from app.core.schemas import DetectedPerson, Statistics, ZoneCounts


class StatisticsService:
    """3-MODUL: Sanash va statistika."""

    def __init__(self) -> None:
        self._seen_ids: dict[str, set[str]] = defaultdict(set)
        self._hourly: dict[str, list[int]] = defaultdict(lambda: [0] * 24)
        self._crossing_times: dict[str, list[float]] = defaultdict(list)
        self._violations: dict[str, int] = defaultdict(int)
        self._last_aggregate: dict[str, datetime] = {}

    def _side_for_person(self, person: DetectedPerson, frame_width: int) -> str:
        if person.in_crosswalk:
            return "crosswalk"
        x_center = (person.bbox[0] + person.bbox[2]) / 2
        third = max(frame_width, 1) / 3
        if x_center < third:
            return "left_sidewalk"
        if x_center > third * 2:
            return "right_sidewalk"
        return "crosswalk"

    def compute_zone_counts(self, persons: list[DetectedPerson], frame_width: int = 1280) -> ZoneCounts:
        left = crosswalk = right = 0
        for person in persons:
            side = self._side_for_person(person, frame_width)
            if side == "left_sidewalk":
                left += 1
            elif side == "crosswalk":
                crosswalk += 1
            else:
                right += 1
        return ZoneCounts(left_side=left, crosswalk=crosswalk, right_side=right)

    def compute_statistics(
        self,
        camera_id: str,
        persons: list[DetectedPerson],
        violation_delta: int = 0,
        frame_width: int = 1280,
    ) -> Statistics:
        seen = self._seen_ids[camera_id]
        new_ids = {person.person_id for person in persons} - seen
        seen.update(new_ids)

        hour = datetime.now(timezone.utc).hour
        if new_ids:
            self._hourly[camera_id][hour] += len(new_ids)

        for person in persons:
            if person.otish_vaqti:
                self._crossing_times[camera_id].append(person.otish_vaqti)

        if violation_delta:
            self._violations[camera_id] += violation_delta

        by_category = Counter(person.category.value for person in persons)
        by_gender = Counter(person.gender.value for person in persons)
        by_direction = Counter(
            "chapdan" if person.direction.value in {"W", "NW", "SW"} else "o'ngdan"
            for person in persons
        )
        by_side = Counter(self._side_for_person(person, frame_width) for person in persons)

        crossing_times = self._crossing_times[camera_id][-100:]
        avg_crossing = round(sum(crossing_times) / len(crossing_times), 2) if crossing_times else 0.0

        hourly = self._hourly[camera_id]
        peak_hour = max(range(24), key=lambda hour: hourly[hour]) if any(hourly) else None

        density_map = self._build_density_map(persons)

        return Statistics(
            total_count=len(persons),
            by_category={
                "piyoda": by_category.get("piyoda", 0),
            },
            by_gender={
                "ayol": by_gender.get("ayol", 0),
                "erkak": by_gender.get("erkak", 0),
                "aniqlanmadi": by_gender.get("aniqlanmadi", 0),
            },
            by_direction=dict(by_direction),
            by_side={
                "left_sidewalk": by_side.get("left_sidewalk", 0),
                "right_sidewalk": by_side.get("right_sidewalk", 0),
                "crosswalk": by_side.get("crosswalk", 0),
            },
            avg_crossing_time=avg_crossing,
            density_map=density_map,
            hourly_flow=hourly,
            peak_hour=peak_hour,
            violation_count=self._violations[camera_id],
        )

    def _build_density_map(self, persons: list[DetectedPerson], grid: int = 8) -> list[list[float]]:
        matrix = [[0.0 for _ in range(grid)] for _ in range(grid)]
        for person in persons:
            x_center = (person.bbox[0] + person.bbox[2]) / 2
            y_center = (person.bbox[1] + person.bbox[3]) / 2
            col = min(grid - 1, max(0, int(x_center / 720 * grid)))
            row = min(grid - 1, max(0, int(y_center / 640 * grid)))
            matrix[row][col] += 1.0

        max_value = max((value for row in matrix for value in row), default=0.0)
        if max_value <= 0:
            return matrix
        return [[round(value / max_value, 3) for value in row] for row in matrix]

    def should_aggregate(self, camera_id: str) -> bool:
        now = datetime.now(timezone.utc)
        last = self._last_aggregate.get(camera_id)
        if not last or (now - last).total_seconds() >= settings.aggregation_interval_sec:
            self._last_aggregate[camera_id] = now
            return True
        return False

    def reset_all(self) -> None:
        self._seen_ids.clear()
        self._hourly.clear()
        self._crossing_times.clear()
        self._violations.clear()
        self._last_aggregate.clear()


statistics_service = StatisticsService()
