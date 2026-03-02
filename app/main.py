from __future__ import annotations

import logging

from vanna import Agent, AgentConfig
from vanna.integrations.postgres import PostgresRunner

from .config import settings
from .logging_config import configure_logging

# 1. Define how to resolve users from requests
from vanna.core.user import UserResolver, User, RequestContext

# 2. Set up LLM and tools
try:  # Prefer core path if available (v2+)
    from vanna.core.registry import ToolRegistry  # type: ignore
except Exception:  # Fallback for older builds
    from vanna import ToolRegistry  # type: ignore
from vanna.servers.fastapi import VannaFastAPIServer  # type: ignore
from vanna.integrations.local.agent_memory import DemoAgentMemory  # type: ignore
from vanna.tools.agent_memory import SaveQuestionToolArgsTool, SearchSavedCorrectToolUsesTool # type: ignore
from vanna.tools import RunSqlTool, VisualizeDataTool  # type: ignore


class SimpleUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        # In production, validate cookies/JWTs here
        user_id = request_context.get_cookie('user_id') or 'demo_user'
        return User(id=user_id, group_memberships=['read_sales'])


# Configure logging early so uvicorn imports get our setup
configure_logging()
logger = logging.getLogger(__name__)
logger.info("Starting VannaFastAPIServer with settings: %s", settings)

# LLM and tools
# Choose LLM based on configured provider
provider = (settings.llm.provider or "anthropic").strip().lower()
logger.info("Initializing LLM provider: %s", provider)

if provider == "ollama":
    # Import locally so the app can still start if Anthropic deps aren't present
    try:
        from vanna.integrations.ollama.llm import OllamaLlmService  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error("Ollama integration is not available: %s", e)
        raise

    host = settings.llm.ollama_base_url or "http://localhost:11434"
    model = settings.llm.ollama_model or "llama3"
    llm = OllamaLlmService(model=model, host=host, temperature=0.2)
elif provider in {"google", "gemini"}:
    try:
        from vanna.integrations.google import GeminiLlmService  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error("Google Gemini integration is not available: %s", e)
        raise

    llm = GeminiLlmService(
        model=(settings.llm.model or "gemini-2.5-pro"),
        api_key=settings.llm.google_api_key,
        temperature=0.2,
    )
elif provider == "openai":
    try:
        from vanna.integrations.openai import OpenAILlmService  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error("OpenAI integration is not available: %s", e)
        raise

    llm = OpenAILlmService(
        model=(settings.llm.model or "gpt-5"),
        api_key=settings.llm.openai_api_key,
        base_url=settings.llm.openai_base_url,
    )
elif provider == "anthropic":
    try:
        from vanna.integrations.anthropic import AnthropicLlmService  # type: ignore
    except Exception as e:  # pragma: no cover
        logger.error("Anthropic integration is not available: %s", e)
        raise

    llm = AnthropicLlmService(model=(settings.llm.model or "claude-sonnet-4-5"))
else:
    raise ValueError(
        f"Unsupported LLM_PROVIDER '{provider}'. Supported providers: anthropic, google, openai, ollama."
    )


def _create_postgres_runner() -> PostgresRunner:
    dsn = (settings.db.dsn or "").strip()
    if dsn:
        logger.debug("Initializing PostgresRunner with DB_DSN")
        return PostgresRunner(connection_string=dsn)

    logger.debug("Initializing PostgresRunner with host/db/user parameters")
    return PostgresRunner(
        host=settings.db.host,
        port=int(settings.db.port) if settings.db.port else 5432,
        database=settings.db.name,
        user=settings.db.user,
        password=settings.db.password,
    )


tools = ToolRegistry()
# ToolRegistry in Vanna v2 uses register_local_tool instead of register
tools.register_local_tool(
    RunSqlTool(sql_runner=_create_postgres_runner()), access_groups=[]
)
tools.register_local_tool(VisualizeDataTool(), access_groups=['admin', 'user'])
agent_memory = DemoAgentMemory(max_items=1000)
tools.register_local_tool(SaveQuestionToolArgsTool(), access_groups=['admin'])
tools.register_local_tool(SearchSavedCorrectToolUsesTool(), access_groups=['admin', 'user'])

# 3. Create agent
agent = Agent(
    llm_service=llm,
    tool_registry=tools,
    user_resolver=SimpleUserResolver(),
    config=AgentConfig(),
    agent_memory=agent_memory
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
