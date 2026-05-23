from app.core.schemas import (
    AgeRange,
    CrosswalkPresence,
    DetectedPerson,
    Direction,
    Gender,
    GroupStatus,
    HandOccupancy,
    PersonCategory,
    SpeedClass,
)
from app.services.statistics import StatisticsService


def _person(bbox: list[float]) -> DetectedPerson:
    return DetectedPerson(
        person_id="p1",
        category=PersonCategory.PIYODA,
        gender=Gender.ANIQLANMADI,
        age_range=AgeRange.ANIQLANMADI,
        clothing_color="qora",
        direction=Direction.E,
        speed_ms=1.2,
        speed_class=SpeedClass.NORMAL,
        group_status=GroupStatus.YOLGIZ,
        qol_band=HandOccupancy.BOSH,
        yol_qaraydi=False,
        peshaxot_ichida=CrosswalkPresence.YOQ,
        in_crosswalk=False,
        bbox=bbox,
        confidence=0.9,
    )


def test_density_map_empty_persons_no_division_error():
    service = StatisticsService()
    stats = service.compute_statistics("cam-1", [])
    assert stats.total_count == 0
    assert stats.density_map == [[0.0] * 8 for _ in range(8)]


def test_density_map_normalizes_values():
    service = StatisticsService()
    stats = service.compute_statistics("cam-2", [_person([100, 100, 200, 200])])
    assert stats.total_count == 1
    assert stats.by_category["piyoda"] == 1
    assert max(max(row) for row in stats.density_map) == 1.0
