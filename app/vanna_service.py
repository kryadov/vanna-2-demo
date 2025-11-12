from __future__ import annotations

import logging
import os
from typing import Any, Optional

from .config import settings
from . import db as db_module

logger = logging.getLogger(__name__)


class VannaService:
    def __init__(self) -> None:
        self._vn: Optional[Any] = None

    def init(self) -> None:
        # Configure provider-specific environment so that vanna can pick it up
        llm = settings.llm
        logger.info("Initializing Vanna with provider=%s", llm.provider)
        if llm.provider == "openai":
            if llm.openai_api_key:
                os.environ.setdefault("OPENAI_API_KEY", llm.openai_api_key)
            if llm.openai_base_url:
                os.environ.setdefault("OPENAI_BASE_URL", llm.openai_base_url)
        elif llm.provider == "google":
            if llm.google_api_key:
                os.environ.setdefault("GOOGLE_API_KEY", llm.google_api_key)
            try:
                import google.generativeai as genai  # type: ignore

                genai.configure(api_key=llm.google_api_key)
            except Exception as e:
                logger.warning("Failed to configure Google GenAI SDK: %s", e)
        elif llm.provider == "ollama":
            if llm.ollama_base_url:
                os.environ.setdefault("OLLAMA_BASE_URL", llm.ollama_base_url)
            if llm.ollama_model:
                os.environ.setdefault("OLLAMA_MODEL", llm.ollama_model)
        else:
            logger.warning("Unknown LLM_PROVIDER '%s' — proceeding with defaults", llm.provider)

        # Attempt to construct a Vanna v2 client. Try a few known entry points defensively.
        vn = None
        errors = []
        for path, factory in [
            ("vanna.VannaDefault", None),
            ("vanna.Vanna", None),
            ("vanna.openai.OpenAI", None),
        ]:
            try:
                module_name, class_name = path.rsplit(".", 1)
                mod = __import__(module_name, fromlist=[class_name])
                cls = getattr(mod, class_name)
                vn = cls()  # type: ignore[call-arg]
                break
            except Exception as e:  # pragma: no cover - best effort
                errors.append(f"{path}: {e}")
                continue

        if vn is None:
            logger.error("Could not initialize Vanna client. Tried: %s", "; ".join(errors))
            raise RuntimeError("Vanna initialization failed; check installation and version")

        # Inject our SQL runner so Vanna can execute SQL when needed
        try:
            setattr(vn, "run_sql", db_module.run_sql)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to attach run_sql to Vanna instance: %s", e)

        self._vn = vn
        logger.info("Vanna initialized successfully")

    def ensure_ready(self) -> None:
        if self._vn is None:
            self.init()

    def generate_sql(self, question: str) -> str:
        self.ensure_ready()
        assert self._vn is not None
        # Try multiple method names to be compatible with v2/v1
        for name in ("generate_sql", "ask_sql", "ask"):  # type: ignore[attr-defined]
            fn = getattr(self._vn, name, None)
            if callable(fn):
                sql = fn(question)
                if isinstance(sql, str):
                    return sql
        raise RuntimeError("Vanna client does not support SQL generation method")


vanna_service = VannaService()
