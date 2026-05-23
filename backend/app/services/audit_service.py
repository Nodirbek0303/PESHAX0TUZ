from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
AUDIT_LOG_PATH = DATA_DIR / "security_audit.log"


class AuditService:
    """6-bosqich: xavfsizlik audit jurnali."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._recent: deque[dict] = deque(maxlen=500)
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        event: str,
        *,
        ip: str | None = None,
        actor: str = "system",
        detail: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "actor": actor,
            "ip": ip,
            "detail": detail,
            "metadata": metadata or {},
        }
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            self._recent.appendleft(entry)
            with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def recent(self, limit: int = 100) -> list[dict]:
        with self._lock:
            return list(self._recent)[:limit]


audit_service = AuditService()
