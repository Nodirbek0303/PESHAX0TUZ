from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import settings
from app.services.audit_service import audit_service
from app.services.intrusion_service import intrusion_service


def security_layers_status() -> dict:
    return {
        "environment": settings.security_environment,
        "layers": [
            {
                "step": 1,
                "name": "Tarmoq va transport himoyasi",
                "status": "active",
                "details": "Security headers, HSTS (production), nginx TLS tavsiya",
            },
            {
                "step": 2,
                "name": "Autentifikatsiya",
                "status": "active",
                "details": "JWT imzolangan token + bcrypt parol hash",
            },
            {
                "step": 3,
                "name": "Avtorizatsiya",
                "status": "active",
                "details": "Admin Bearer JWT, sensor X-Sensor-Key, public read-only",
            },
            {
                "step": 4,
                "name": "Brute-force va DDoS himoyasi",
                "status": "active",
                "details": (
                    f"Login: {settings.security_login_max_attempts} urinish / "
                    f"{settings.security_login_lockout_minutes} daq blok; "
                    f"Rate: {settings.security_rate_limit_per_minute}/daq"
                ),
            },
            {
                "step": 5,
                "name": "Kirish validatsiyasi",
                "status": "active",
                "details": f"Pydantic sxemalar, max body {settings.security_max_body_bytes // 1024} KB",
            },
            {
                "step": 6,
                "name": "Audit jurnali",
                "status": "active",
                "details": "security_audit.log — barcha admin va xavfsizlik hodisalari",
            },
            {
                "step": 7,
                "name": "Ma'lumotlar maxfiyligi",
                "status": "active" if settings.admin_password_hash else "warning",
                "details": (
                    "Parol hash o'rnatilgan"
                    if settings.admin_password_hash
                    else "Production uchun ADMIN_PASSWORD_HASH o'rnating"
                ),
            },
            {
                "step": 8,
                "name": "Intrusion Detection",
                "status": "active",
                "details": f"Bloklangan IP: {intrusion_service.status()['blocked_ips']}",
            },
        ],
        "sensor_key_required": settings.security_require_sensor_key,
        "docs_enabled": settings.security_enable_docs,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def get_security_report() -> dict:
    return {
        "status": security_layers_status(),
        "intrusion": intrusion_service.status(),
        "audit_recent": audit_service.recent(limit=30),
        "intrusion_alerts": intrusion_service.recent_alerts(limit=20),
    }
