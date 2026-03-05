from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def _optional(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer") from exc


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be a number") from exc


def _bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(slots=True)
class Settings:
    bot_token: str
    dadata_api_key: str
    webhook_base_url: str
    webhook_path: str
    webhook_secret: str
    host: str
    port: int
    cache_ttl_seconds: int
    session_ttl_seconds: int
    dadata_rps_limit: int
    request_timeout_seconds: float
    redis_url: str | None
    drop_pending_updates: bool
    max_connections: int
    log_level: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    webhook_base_url = _required("WEBHOOK_BASE_URL").rstrip("/")
    webhook_path = _optional("WEBHOOK_PATH", "/telegram/webhook") or "/telegram/webhook"
    if not webhook_path.startswith("/"):
        webhook_path = "/" + webhook_path

    webhook_secret = _required("TELEGRAM_WEBHOOK_SECRET")

    return Settings(
        bot_token=_required("BOT_TOKEN"),
        dadata_api_key=_required("DADATA_API_KEY"),
        webhook_base_url=webhook_base_url,
        webhook_path=webhook_path,
        webhook_secret=webhook_secret,
        host=_optional("HOST", "0.0.0.0") or "0.0.0.0",
        port=_int("PORT", 8080),
        cache_ttl_seconds=_int("CACHE_TTL_SECONDS", 6 * 60 * 60),
        session_ttl_seconds=_int("SESSION_TTL_SECONDS", 2 * 60 * 60),
        dadata_rps_limit=max(1, _int("DADATA_RPS_LIMIT", 8)),
        request_timeout_seconds=max(1.0, _float("REQUEST_TIMEOUT_SECONDS", 10.0)),
        redis_url=_optional("REDIS_URL"),
        drop_pending_updates=_bool("DROP_PENDING_UPDATES", False),
        max_connections=max(1, _int("DADATA_MAX_CONNECTIONS", 10)),
        log_level=(_optional("LOG_LEVEL", "INFO") or "INFO").upper(),
    )
