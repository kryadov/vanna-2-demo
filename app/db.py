from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine

from .config import settings

logger = logging.getLogger(__name__)


def _build_sqlalchemy_url() -> str:
    db = settings.db
    if db.dsn:
        return db.dsn

    if db.dialect == "postgres":
        user = db.user or "postgres"
        password = db.password or ""
        host = db.host or "localhost"
        port = db.port or "5432"
        name = db.name or "postgres"
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"
    elif db.dialect == "oracle":
        user = db.user or "system"
        password = db.password or "oracle"
        host = db.host or "localhost"
        port = db.port or "1521"
        service = db.name or "FREEPDB1"
        # oracledb thin driver with service name
        return (
            f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service}"
        )
    else:
        raise ValueError(f"Unsupported DB_DIALECT: {db.dialect}")


_engine: Optional[Engine] = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        url = _build_sqlalchemy_url()
        logger.info("Creating SQLAlchemy engine for %s", url.split("@")[0] + "@…")
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


@contextmanager
def connect() -> Iterator:
    engine = get_engine()
    with engine.connect() as conn:
        yield conn


def run_sql(sql: str) -> pd.DataFrame:
    logger.info("Executing SQL: %s", sql)
    with connect() as conn:
        df = pd.read_sql(text(sql), conn)
    logger.info("Query returned %d rows and %d columns", df.shape[0], df.shape[1])
    return df


def healthcheck() -> dict:
    try:
        test_sql = "SELECT 1" if settings.db.dialect == "postgres" else "SELECT 1 FROM dual"
        df = run_sql(test_sql)
        ok = not df.empty
        return {"database": "ok" if ok else "no rows"}
    except Exception as e:
        logger.exception("Database healthcheck failed: %s", e)
        return {"database": f"error: {e}"}
