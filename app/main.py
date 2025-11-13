from __future__ import annotations

import logging
from pathlib import Path

from vanna.integrations.postgres import PostgresRunner

from .config import settings
from .logging_config import configure_logging

# 1. Define how to resolve users from requests
from vanna.core.user import UserResolver, User, RequestContext

# 2. Set up LLM and tools
from vanna import Agent  # type: ignore
try:  # Prefer core path if available (v2+)
    from vanna.core.registry import ToolRegistry  # type: ignore
except Exception:  # Fallback for older builds
    from vanna import ToolRegistry  # type: ignore
from vanna.servers.fastapi import VannaFastAPIServer  # type: ignore
from vanna.integrations.local.agent_memory import DemoAgentMemory  # type: ignore
from vanna.tools import RunSqlTool  # type: ignore
from vanna.integrations.sqlite import SqliteRunner  # type: ignore


class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        # In production, validate cookies/JWTs here
        user_id = request_context.get_cookie('user_id') or 'demo_user'
        return User(id=user_id, group_memberships=['read_sales'])


# Configure logging early so uvicorn imports get our setup
configure_logging()
logging.getLogger(__name__).info("Starting VannaFastAPIServer with settings: %s", settings)

# LLM and tools
# Choose LLM based on configured provider
provider = (settings.llm.provider or "").lower()
logging.getLogger(__name__).info("Initializing LLM provider: %s", provider or "<unset>")

if provider == "ollama":
    # Import locally so the app can still start if Anthropic deps aren't present
    try:
        from vanna.integrations.ollama.llm import OllamaLlmService  # type: ignore
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).error("Ollama integration is not available: %s", e)
        raise

    host = settings.llm.ollama_base_url or "http://localhost:11434"
    model = settings.llm.ollama_model or "llama3"
    llm = OllamaLlmService(model=model, host=host, temperature=0.2)
else:
    # Default to Anthropic when provider is not 'ollama'
    try:
        from vanna.integrations.anthropic import AnthropicLlmService  # type: ignore
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).error("Anthropic integration is not available: %s", e)
        raise

    llm = AnthropicLlmService(model=(settings.llm.model or "claude-sonnet-4-5"))
tools = ToolRegistry()
# ToolRegistry in Vanna v2 uses register_local_tool instead of register
tools.register_local_tool(
    RunSqlTool(sql_runner=PostgresRunner(connection_string=settings.db)), access_groups=[]
)

# 3. Create agent
agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=SimpleUserResolver(),
    agent_memory=DemoAgentMemory(),
)

# 4. Create and run server
server = VannaFastAPIServer(agent)
app = server.create_app()  # FastAPI application


def main() -> None:
    """Run the FastAPI app with uvicorn using configured host/port."""
    try:
        import uvicorn  # type: ignore
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).error("Uvicorn is required to run the FastAPI app: %s", e)
        raise

    uvicorn.run(
        app,
        host=settings.app.host,
        port=settings.app.port,
        log_level=settings.log.level.lower(),
    )


if __name__ == "__main__":
    main()
