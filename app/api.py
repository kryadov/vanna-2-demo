from __future__ import annotations

import logging
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from .config import settings
from .db import healthcheck as db_healthcheck, run_sql
from .vanna_service import vanna_service

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health() -> Any:
    logger.info("Health check requested")
    db_status = db_healthcheck()
    return jsonify(
        {
            "status": "ok",
            "db": db_status,
            "llm_provider": settings.llm.provider,
        }
    )


@api_bp.get("/db-test")
def db_test() -> Any:
    try:
        sql = "SELECT 1" if settings.db.dialect == "postgres" else "SELECT 1 FROM dual"
        df = run_sql(sql)
        return jsonify({"sql": sql, "rows": df.to_dict(orient="records")})
    except Exception as e:
        logger.exception("DB test failed: %s", e)
        return jsonify({"error": str(e)}), 500


@api_bp.post("/ask")
def ask() -> Any:
    data: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    execute = bool(data.get("execute", False))
    limit = int(data.get("limit", 50))

    if not question:
        return jsonify({"error": "Missing 'question'"}), 400

    try:
        sql = vanna_service.generate_sql(question)
        result: Dict[str, Any] = {"sql": sql}
        if execute and sql:
            # naive LIMIT for Postgres; for Oracle, use FETCH FIRST N ROWS ONLY
            if settings.db.dialect == "postgres" and "limit" not in sql.lower():
                sql_to_run = f"SELECT * FROM ( {sql} ) AS sub LIMIT {limit}"
            elif settings.db.dialect == "oracle" and "fetch first" not in sql.lower():
                sql_to_run = f"SELECT * FROM ( {sql} ) FETCH FIRST {limit} ROWS ONLY"
            else:
                sql_to_run = sql
            df = run_sql(sql_to_run)
            result["rows"] = df.to_dict(orient="records")
            result["columns"] = list(df.columns)
        return jsonify(result)
    except Exception as e:
        logger.exception("/api/ask failed: %s", e)
        return jsonify({"error": str(e)}), 500
