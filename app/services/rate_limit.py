from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Callable

from starlette.requests import Request

QUOTA_MESSAGE = "OOPS! Today's limit is reached. Try again tomorrow. Thank you!"


def _env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(value, minimum)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class LimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    scope: str = "ip"


class DailyLimiter:
    """Thread-safe daily counter for a single action type.

    Counters are kept in memory because the application already runs as a
    single process with in-memory jobs. A zero limit disables that dimension.
    """

    def __init__(
        self,
        *,
        per_ip: int,
        global_limit: int,
        clock: Callable[[], datetime] = _utcnow,
    ) -> None:
        self.per_ip = max(per_ip, 0)
        self.global_limit = max(global_limit, 0)
        self._clock = clock
        self._lock = threading.Lock()
        self._day = None
        self._by_ip: dict[str, int] = {}
        self._total = 0

    def _sync_day(self, now: datetime) -> None:
        today = now.date()
        if today != self._day:
            self._day = today
            self._by_ip.clear()
            self._total = 0

    def _retry_after(self, now: datetime) -> int:
        tomorrow = datetime.combine(
            now.date() + timedelta(days=1),
            time.min,
            tzinfo=timezone.utc,
        )
        return max(1, int((tomorrow - now).total_seconds()))

    def _decision(self, key: str, now: datetime) -> LimitResult:
        retry_after = self._retry_after(now)
        used = self._by_ip.get(key, 0)
        if self.per_ip and used >= self.per_ip:
            return LimitResult(False, self.per_ip, 0, retry_after, "ip")
        if self.global_limit and self._total >= self.global_limit:
            return LimitResult(False, self.global_limit, 0, retry_after, "global")
        if self.per_ip and self.global_limit:
            remaining = min(self.per_ip - used, self.global_limit - self._total)
        elif self.per_ip:
            remaining = self.per_ip - used
        elif self.global_limit:
            remaining = self.global_limit - self._total
        else:
            remaining = -1
        return LimitResult(True, self.per_ip or self.global_limit, remaining, retry_after)

    def check(self, key: str) -> LimitResult:
        with self._lock:
            now = self._clock()
            self._sync_day(now)
            return self._decision(key, now)

    def consume(self, key: str) -> LimitResult:
        with self._lock:
            now = self._clock()
            self._sync_day(now)
            result = self._decision(key, now)
            if not result.allowed:
                return result
            self._by_ip[key] = self._by_ip.get(key, 0) + 1
            self._total += 1
            return result


_RATE_LIMITS_ENABLED = _env_bool("RATE_LIMIT_ENABLED", True)
_TRUST_PROXY_HEADERS = _env_bool(
    "TRUST_PROXY_HEADERS",
    bool(os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID")),
)

job_limiter = DailyLimiter(
    per_ip=_env_int("DAILY_JOB_LIMIT_PER_IP", 3),
    global_limit=_env_int("DAILY_JOB_LIMIT_GLOBAL", 25),
)
chat_limiter = DailyLimiter(
    per_ip=_env_int("DAILY_CHAT_LIMIT_PER_IP", 40),
    global_limit=_env_int("DAILY_CHAT_LIMIT_GLOBAL", 400),
)


def rate_limits_enabled() -> bool:
    return _RATE_LIMITS_ENABLED


def client_key(request: Request) -> str:
    if _TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            return forwarded.split(",", 1)[0].strip() or "unknown"
        real_ip = request.headers.get("x-real-ip", "")
        if real_ip:
            return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
