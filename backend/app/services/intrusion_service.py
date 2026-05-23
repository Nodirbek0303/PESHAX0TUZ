from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock


@dataclass
class BlockedIp:
    until: datetime
    reason: str


class IntrusionService:
    """4 va 8-bosqich: brute-force, rate limit, IP bloklash."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._login_failures: dict[str, deque[datetime]] = defaultdict(deque)
        self._request_times: dict[str, deque[datetime]] = defaultdict(deque)
        self._blocked: dict[str, BlockedIp] = {}
        self._alerts: deque[dict] = deque(maxlen=200)

    def _prune(self, bucket: deque[datetime], window_sec: int) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_sec)
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

    def is_blocked(self, ip: str) -> tuple[bool, str | None]:
        with self._lock:
            blocked = self._blocked.get(ip)
            if not blocked:
                return False, None
            if datetime.now(timezone.utc) >= blocked.until:
                del self._blocked[ip]
                return False, None
            return True, blocked.reason

    def block_ip(self, ip: str, minutes: int, reason: str) -> None:
        with self._lock:
            self._blocked[ip] = BlockedIp(
                until=datetime.now(timezone.utc) + timedelta(minutes=minutes),
                reason=reason,
            )
            self._alerts.appendleft(
                {
                    "type": "IP_BLOCKED",
                    "ip": ip,
                    "reason": reason,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

    def record_login_failure(self, ip: str, max_attempts: int, lockout_minutes: int) -> bool:
        """Returns True if IP was blocked."""
        with self._lock:
            bucket = self._login_failures[ip]
            bucket.append(datetime.now(timezone.utc))
            self._prune(bucket, lockout_minutes * 60)
            if len(bucket) >= max_attempts:
                self.block_ip(ip, lockout_minutes, "Ko'p marta noto'g'ri admin parol")
                bucket.clear()
                return True
        return False

    def clear_login_failures(self, ip: str) -> None:
        with self._lock:
            self._login_failures.pop(ip, None)

    def check_rate_limit(self, ip: str, limit: int, window_sec: int = 60) -> bool:
        """Returns True if allowed, False if exceeded."""
        with self._lock:
            bucket = self._request_times[ip]
            bucket.append(datetime.now(timezone.utc))
            self._prune(bucket, window_sec)
            if len(bucket) > limit:
                self._alerts.appendleft(
                    {
                        "type": "RATE_LIMIT",
                        "ip": ip,
                        "count": len(bucket),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                return False
            return True

    def recent_alerts(self, limit: int = 20) -> list[dict]:
        with self._lock:
            return list(self._alerts)[:limit]

    def status(self) -> dict:
        with self._lock:
            return {
                "blocked_ips": len(self._blocked),
                "tracked_ips": len(self._request_times),
                "recent_alerts": len(self._alerts),
            }


intrusion_service = IntrusionService()
