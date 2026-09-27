import logging
import time

from app.core.config import settings

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_db: Database | None = None

def init_db():
    global _client, _db
    if _client is not None:
        return _db

    max_pool_size = settings.mongo_max_pool_size
    min_pool_size = settings.mongo_min_pool_size
    max_idle_ms = settings.mongo_max_idle_ms
    wait_timeout_ms = settings.mongo_wait_timeout_ms

    if max_pool_size <= 0:
        raise ValueError("Configuration error: MONGO_MAX_POOL_SIZE must be > 0")
    if min_pool_size < 0:
        raise ValueError("Configuration error: MONGO_MIN_POOL_SIZE must be >= 0")
    if min_pool_size > max_pool_size:
        raise ValueError(
            "Configuration error: MONGO_MIN_POOL_SIZE cannot be greater than MONGO_MAX_POOL_SIZE"
        )
    if max_idle_ms < 0:
        raise ValueError("Configuration error: MONGO_MAX_IDLE_TIME_MS must be >= 0")
    if wait_timeout_ms <= 0:
        raise ValueError("Configuration error: MONGO_WAIT_QUEUE_TIMEOUT_MS must be > 0")

    max_attempts = 5

    _client = MongoClient(
        settings.mongo_uri,
        maxPoolSize=max_pool_size,
        minPoolSize=min_pool_size,
        maxIdleTimeMS=max_idle_ms,
        waitQueueTimeoutMS=wait_timeout_ms,
        serverSelectionTimeoutMS=2000,
    )

    logger.info({
        "event": "mongodb_connection_start",
        "msg": "Waiting for database to start...",
    })

    for attempt in range(1, max_attempts + 1):
        try:
            _db = _client[settings.mongo_db]
            _client.admin.command("ping")

            logger.info({
                "event": "mongodb_connection_success",
                "msg": "Successfully connected to MongoDB database",
                "database": settings.mongo_db,
            })
            return _db

        except ServerSelectionTimeoutError as e:
            sleep_time = attempt + 1

            if attempt == max_attempts:
                logger.critical({
                    "event": "mongodb_connection_error",
                    "msg": f"Critical Error: Could not connect to MongoDB after {max_attempts} attempts. Stopping the server...",
                }, exc_info=True)
                raise SystemExit("MongoDB connection failed") from e

            logger.warning({
                "event": "mongodb_connection_retry",
                "msg": f"Database is not ready yet (Attempt {attempt}/{max_attempts}). Retrying in {sleep_time}s...",
            })
            time.sleep(sleep_time)

        except Exception as e:
            logger.critical({
                "event": "mongodb_unexpected_error",
                "msg": f"Unexpected error during MongoDB initialization: {e}",
            }, exc_info=True)
            raise SystemExit("MongoDB unexpected error") from e


def get_db() -> Database:
    if _db is None:
        raise RuntimeError("mongo database is not initialized")
    return _db


def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
        logger.info({
            "event": "mongodb_connection_closed",
            "msg": "MongoDB connection successfully closed",
        })
