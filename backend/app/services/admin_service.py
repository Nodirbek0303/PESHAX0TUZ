from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings
from app.core.security import (
    create_admin_token,
    decode_admin_token,
    hash_token_fingerprint,
    verify_admin_password,
)
from app.core.schemas import CameraStatus
from app.services.alerts import alert_service
from app.services.audit_service import audit_service
from app.services.camera_manager import camera_manager
from app.services.intrusion_service import intrusion_service
from app.services.pipeline import pipeline_service


class AdminService:
    def __init__(self) -> None:
        self._revoked_jti: set[str] = set()

    def login(self, password: str, ip: str = "unknown") -> tuple[str, int] | None:
        blocked, reason = intrusion_service.is_blocked(ip)
        if blocked:
            audit_service.log("ADMIN_LOGIN_BLOCKED", ip=ip, actor="admin", detail=reason)
            return None

        if not verify_admin_password(password):
            blocked_now = intrusion_service.record_login_failure(
                ip,
                settings.security_login_max_attempts,
                settings.security_login_lockout_minutes,
            )
            audit_service.log("ADMIN_LOGIN_FAIL", ip=ip, actor="admin")
            if blocked_now:
                audit_service.log("INTRUSION_ALERT", ip=ip, detail="IP login bloklandi")
            return None

        intrusion_service.clear_login_failures(ip)
        token, expires, jti = create_admin_token()
        audit_service.log(
            "ADMIN_LOGIN_OK",
            ip=ip,
            actor="admin",
            metadata={"jti": jti, "expires": expires.isoformat()},
        )
        return token, settings.admin_token_ttl_hours

    def verify_token(self, token: str | None) -> bool:
        if not token:
            return False
        payload = decode_admin_token(token)
        if not payload:
            return False
        jti = payload.get("jti")
        if jti and jti in self._revoked_jti:
            return False
        return payload.get("sub") == "admin"

    def logout(self, token: str, ip: str = "unknown") -> None:
        payload = decode_admin_token(token)
        if payload and payload.get("jti"):
            self._revoked_jti.add(str(payload["jti"]))
        audit_service.log(
            "ADMIN_LOGOUT",
            ip=ip,
            actor="admin",
            metadata={"token": hash_token_fingerprint(token)},
        )

    def build_dashboard(self) -> dict:
        cameras = camera_manager.list_cameras()
        online = sum(1 for camera in cameras if camera.status == CameraStatus.ONLINE)
        total_people = 0
        total_crosswalk = 0
        total_violations = 0
        by_gender: dict[str, int] = {"ayol": 0, "erkak": 0, "aniqlanmadi": 0}
        by_category: dict[str, int] = {"piyoda": 0}
        by_direction: dict[str, int] = {"chapdan": 0, "o'ngdan": 0}
        by_side: dict[str, int] = {"left_sidewalk": 0, "crosswalk": 0, "right_sidewalk": 0}
        hourly_flow = [0] * 24
        recent_detections: list[dict] = []
        camera_cards: list[dict] = []
        region_stats: dict[str, dict] = {}

        for camera in cameras:
            frame = pipeline_service.process_camera(camera.camera_id)
            stats = frame.statistics
            zones = frame.zone_counts
            total_people += stats.total_count
            total_crosswalk += zones.crosswalk
            total_violations += stats.violation_count

            for key, value in stats.by_gender.items():
                by_gender[key] = by_gender.get(key, 0) + value
            for key, value in stats.by_category.items():
                by_category[key] = by_category.get(key, 0) + value
            for key, value in stats.by_direction.items():
                by_direction[key] = by_direction.get(key, 0) + value
            for key, value in stats.by_side.items():
                by_side[key] = by_side.get(key, 0) + value
            for hour, count in enumerate(stats.hourly_flow):
                hourly_flow[hour] += count

            for person in frame.detected_persons[:3]:
                recent_detections.append(
                    {
                        "timestamp": frame.timestamp.isoformat(),
                        "camera_id": camera.camera_id,
                        "camera_name": camera.camera_name,
                        "camera_number": camera.camera_number,
                        "region": camera.region,
                        "city": camera.city,
                        "person_id": person.person_id,
                        "category": person.category.value,
                        "gender": person.gender.value,
                        "in_crosswalk": person.in_crosswalk,
                        "confidence": person.confidence,
                    }
                )

            camera_cards.append(
                {
                    "camera_id": camera.camera_id,
                    "camera_name": camera.camera_name,
                    "camera_number": camera.camera_number,
                    "region": camera.region,
                    "city": camera.city,
                    "district": camera.district,
                    "street": camera.street,
                    "status": camera.status.value,
                    "gps_coords": camera.gps_coords.model_dump(),
                    "people_count": stats.total_count,
                    "crosswalk_count": zones.crosswalk,
                    "vehicles": len(frame.detected_vehicles),
                    "snapshot_url": frame.snapshot_url,
                    "alerts_count": len(frame.active_alerts),
                }
            )

            region = camera.region
            bucket = region_stats.setdefault(
                region,
                {"region": region, "cameras": 0, "online": 0, "people": 0},
            )
            bucket["cameras"] += 1
            if camera.status == CameraStatus.ONLINE:
                bucket["online"] += 1
            bucket["people"] += stats.total_count

        alerts = alert_service.recent_all(limit=30)
        danger_alerts = sum(1 for alert in alerts if alert.severity.value == "RED")

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_cameras": len(cameras),
                "online_cameras": online,
                "offline_cameras": len(cameras) - online,
                "people_now": total_people,
                "crosswalk_now": total_crosswalk,
                "today_flow": sum(hourly_flow),
                "active_alerts": len(alerts),
                "danger_alerts": danger_alerts,
                "violations": total_violations,
            },
            "demographics": {
                "by_category": by_category,
                "by_gender": by_gender,
                "by_direction": by_direction,
                "by_side": by_side,
            },
            "hourly_flow": hourly_flow,
            "regions": list(region_stats.values()),
            "cameras": camera_cards,
            "alerts": [alert.model_dump(mode="json") for alert in alerts[:15]],
            "recent_detections": recent_detections[:20],
        }


admin_service = AdminService()
