from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root by default
load_dotenv(override=False)


@dataclass
class AppConfig:
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("APP_DEBUG", "false").lower() in {"1", "true", "yes", "on"}


@dataclass
class LogConfig:
    level: str = os.getenv("LOG_LEVEL", "INFO")


@dataclass
class DBConfig:
    dialect: str = os.getenv("DB_DIALECT", "postgres").lower()  # postgres|oracle
    host: Optional[str] = os.getenv("DB_HOST")
    port: Optional[str] = os.getenv("DB_PORT")
    user: Optional[str] = os.getenv("DB_USER")
    password: Optional[str] = os.getenv("DB_PASSWORD")
    name: Optional[str] = os.getenv("DB_NAME")  # postgres database name; oracle service name (by default)
    schema: Optional[str] = os.getenv("DB_SCHEMA")
    # Optional: direct DSN/URL; if provided, overrides individual parts
    dsn: Optional[str] = os.getenv("DB_DSN")


@dataclass
class LLMConfig:
    provider: str = os.getenv("LLM_PROVIDER", "openai").lower()  # openai|google|ollama
    model: Optional[str] = os.getenv("LLM_MODEL")
    # OpenAI
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_base_url: Optional[str] = os.getenv("OPENAI_BASE_URL")
    # Google
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    # Ollama
    ollama_base_url: Optional[str] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: Optional[str] = os.getenv("OLLAMA_MODEL", "llama3")


@dataclass
class Settings:
    app: AppConfig = AppConfig()
    log: LogConfig = LogConfig()
    db: DBConfig = DBConfig()
    llm: LLMConfig = LLMConfig()


settings = Settings()
