from __future__ import annotations

from app.services.alerts import alert_service
from app.services.camera_manager import camera_manager
from app.services.sensor_service import sensor_service
from app.services.statistics import statistics_service


def reset_all_runtime_data() -> dict:
    camera_summary = camera_manager.reset_all()
    statistics_service.reset_all()
    alert_service.reset_all()
    sensor_service.reset_all()
    return {
        "ok": True,
        "message": "Barcha ma'lumotlar nolga tushirildi",
        "cameras": camera_summary,
    }
