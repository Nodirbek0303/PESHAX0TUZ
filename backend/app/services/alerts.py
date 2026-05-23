from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings
from app.core.schemas import (
    Alert,
    AlertSeverity,
    AlertType,
    CameraStatus,
    DetectedPerson,
)
from app.services.camera_manager import camera_manager


ALERT_TEXT: dict[AlertType, tuple[str, str]] = {
    AlertType.QIZIL_CHIROQ_BUZISH: (
        "Piyoda qizil chiroqda peshaxotni kesib o'tmoqda.",
        "Yo'l harakati nazoratchisiga darhol xabar bering; signalizatsiyani faollashtiring.",
    ),
    AlertType.TRANSPORT_TOQNASHUV: (
        "Transport bilan to'qnashuv xavfi 2 soniyadan kam.",
        "Yaqin atrofdagi svetofor va audio ogohlantirishni yoqing.",
    ),
    AlertType.GURUH_TOSIQCHI: (
        "6+ kishi peshaxotni to'sib qo'ydi.",
        "Oqimni tartibga solish va qo'shimcha vaqt berishni ko'rib chiqing.",
    ),
    AlertType.GAVJUMLIK_OSHDI: (
        "Peshaxotdagi odamlar soni limitdan oshdi.",
        "Qo'shimcha o'tish vaqtini yoki politsiya nazoratini ko'rib chiqing.",
    ),
    AlertType.KAMERA_OFFLINE: (
        "Kamera ulanishi uzildi.",
        "Texnik xizmatga zudlik bilan xabar bering.",
    ),
    AlertType.TIZIM_YUKLANISH: (
        "Tizim yuklanishi 85% dan oshdi.",
        "Inference navbatini optimallashtiring yoki qo'shimcha GPU qo'shing.",
    ),
}


class AlertService:
    """4-MODUL: faqat kameradan o'lchanadigan ma'lumotlarga asoslangan ogohlantirishlar."""

    def __init__(self) -> None:
        self._active: dict[str, list[Alert]] = {}

    def _make_alert(
        self,
        camera_id: str,
        alert_type: AlertType,
        severity: AlertSeverity,
        person: DetectedPerson | None = None,
    ) -> Alert:
        description, action = ALERT_TEXT[alert_type]
        location = camera_manager.location_payload(camera_id) or {}
        return Alert(
            timestamp=datetime.now(timezone.utc),
            camera_id=camera_id,
            location=location,
            alert_type=alert_type,
            severity=severity,
            person_id=person.person_id if person else None,
            category=person.category.value if person else None,
            description=description,
            recommended_action=action,
            snapshot_url=f"{settings.api_prefix}/snapshot/{camera_id}",
        )

    def evaluate(
        self,
        camera_id: str,
        persons: list[DetectedPerson],
        traffic_light_red: bool = False,
        vehicle_proximity_sec: float | None = None,
        gpu_load: float = 0.0,
    ) -> list[Alert]:
        alerts: list[Alert] = []
        crosswalk_persons = [person for person in persons if person.in_crosswalk]

        if traffic_light_red:
            for person in crosswalk_persons:
                alerts.append(
                    self._make_alert(
                        camera_id,
                        AlertType.QIZIL_CHIROQ_BUZISH,
                        AlertSeverity.RED,
                        person,
                    )
                )

        if vehicle_proximity_sec is not None and vehicle_proximity_sec < settings.vehicle_proximity_alert_sec:
            for person in crosswalk_persons[:1]:
                alerts.append(
                    self._make_alert(
                        camera_id,
                        AlertType.TRANSPORT_TOQNASHUV,
                        AlertSeverity.RED,
                        person,
                    )
                )

        if len(crosswalk_persons) >= 6:
            alerts.append(
                self._make_alert(camera_id, AlertType.GURUH_TOSIQCHI, AlertSeverity.YELLOW)
            )

        if len(crosswalk_persons) > settings.crosswalk_density_limit:
            alerts.append(
                self._make_alert(camera_id, AlertType.GAVJUMLIK_OSHDI, AlertSeverity.BLUE)
            )

        camera = camera_manager.get_camera(camera_id)
        if camera and camera.status == CameraStatus.OFFLINE:
            alerts.append(
                self._make_alert(camera_id, AlertType.KAMERA_OFFLINE, AlertSeverity.BLUE)
            )

        if gpu_load > settings.gpu_load_alert_threshold:
            alerts.append(
                self._make_alert(camera_id, AlertType.TIZIM_YUKLANISH, AlertSeverity.BLUE)
            )

        self._active[camera_id] = alerts[-50:]
        return alerts

    def get_active(self, camera_id: str) -> list[Alert]:
        return self._active.get(camera_id, [])

    def recent_all(self, limit: int = 20) -> list[Alert]:
        combined: list[Alert] = []
        for alerts in self._active.values():
            combined.extend(alerts)
        combined.sort(key=lambda alert: alert.timestamp, reverse=True)
        return combined[:limit]

    def reset_all(self) -> None:
        self._active.clear()


alert_service = AlertService()
