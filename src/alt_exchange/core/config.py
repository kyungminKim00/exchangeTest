from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./alt_exchange.db")
    jwt_secret: str = os.getenv("JWT_SECRET", "local-secret")
    ws_enabled: bool = _env_bool("WS_ENABLED", False)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
