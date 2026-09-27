import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

Environment = Literal["development", "production"]

def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env(Path(__file__).resolve().parents[2] / ".env")


def _req(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _req_int(name: str) -> int:
    return int(_req(name))

def _environment() -> Environment:
    value = _req("ENVIRONMENT").lower()
    if value not in ("development", "production"):
        raise RuntimeError(
            f"ENVIRONMENT must be 'development' or 'production', got: {value!r}"
        )
    return value


def _build_mongo_uri() -> str:
    user = quote_plus(_req("MONGO_USER"))
    password = quote_plus(_req("MONGO_PASSWORD"))
    host = _req("MONGO_HOST")
    port = _req("MONGO_PORT")
    return f"mongodb://{user}:{password}@{host}:{port}/"


@dataclass(frozen=True)
class Settings:
    environment=_environment()
    mongo_uri: str
    mongo_db: str
    mongo_max_pool_size: int
    mongo_min_pool_size: int
    mongo_wait_timeout_ms: int
    mongo_max_idle_ms: int
    token_secret: str
    access_ttl_seconds: int
    refresh_ttl_seconds: int

    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings(
    mongo_uri=_build_mongo_uri(),
    mongo_db=_req("MONGO_DB"),
    mongo_max_pool_size=_req_int("MONGO_MAX_POOL_SIZE"),
    mongo_max_idle_ms=_req_int("MONGO_MAX_IDLE_TIME_MS"),
    mongo_min_pool_size=_req_int("MONGO_MIN_POOL_SIZE"),
    mongo_wait_timeout_ms=_req_int("MONGO_WAIT_QUEUE_TIMEOUT_MS"),
    token_secret=_req("TOKEN_SECRET"),
    access_ttl_seconds=_req_int("ACCESS_TTL_SECONDS"),
    refresh_ttl_seconds=_req_int("REFRESH_TTL_SECONDS"),
)