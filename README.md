### Vanna AI v2 — FastAPI Server App

This app is a minimal reference implementation that runs a Vanna AI v2 Agent with a FastAPI server and a built‑in chat UI. It is configured via a `.env` file, uses the `uv` Python package manager, and runs on Python 3.13.

- Built‑in UI: `GET /` (served by Vanna’s FastAPI server)
- Health: `GET /health`
- Chat API (v2):
  - `POST /api/vanna/v2/chat_sse` (streaming via Server‑Sent Events)
  - `POST /api/vanna/v2/chat_poll` (polling)
  - `WS   /api/vanna/v2/chat_websocket` (WebSocket)
- FastAPI docs: `GET /docs`
- LLM providers: Anthropic (default), Ollama
- Logging: INFO level by default

Reference: Vanna v2 README — https://github.com/vanna-ai/vanna/blob/v2/README.md


### Prerequisites

- Install `uv` (see https://docs.astral.sh/uv/):
  - Windows (PowerShell):
    ```powershell
    iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex
    ```
- Ensure Python 3.13 is available via `uv`:
  ```powershell
  uv python install 3.13
  ```
- Optional: Ensure an Ollama server is running if you plan to use `LLM_PROVIDER=ollama`:
  - https://ollama.ai
  - Pull a model, e.g.: `ollama pull llama3`


### Setup

1) Clone and enter the project folder, then create your environment file:
   ```powershell
   Copy-Item .env.example .env
   # Edit .env to set DB and LLM credentials
   ```

2) Install dependencies using uv (reads `pyproject.toml`):
   ```powershell
   uv sync
   ```

3) Vanna v2 dependency is already declared in `pyproject.toml` from the v2 branch. If you need to force-reinstall (as sometimes recommended by Vanna docs), you can run:
   ```powershell
   uv run pip install --force-reinstall --no-cache-dir "vanna[flask,anthropic] @ git+https://github.com/vanna-ai/vanna.git@v2"
   ```


### Configuration (.env)

See `.env.example` for all options. Key variables:

- App and logging
  - `APP_HOST` (default `0.0.0.0`), `APP_PORT` (default `8000`), `APP_DEBUG` (`true`/`false`)
  - `LOG_LEVEL` (default `INFO`)

- LLM provider
  - Default: Anthropic Sonnet (`LLM_MODEL` can override model name)
  - Ollama: set `LLM_PROVIDER=ollama`
    - `OLLAMA_BASE_URL` (default `http://localhost:11434`)
    - `OLLAMA_MODEL` (default `llama3`)

Note: This app no longer includes the custom Flask REST endpoints or the SQLAlchemy database runner. If you want to connect tools to your database (e.g., Postgres/Oracle), register an appropriate `RunSqlTool` in `app/main.py` (instead of the default SQLite example).


### Optional: Database tooling

By default, `app/main.py` registers a `RunSqlTool` with a SQLite runner pointed at `./data.db` as a simple example. To target your own database (Postgres, Oracle, etc.), replace that tool with the appropriate Vanna integration in `main.py` and ensure required drivers are installed.


### Running the app

- Development server:
  ```powershell
  uv run vanna_app
  # or
  uv run python -m app.main
  ```

- Open in your browser: http://localhost:8000
  - Built‑in UI: `GET /`
  - Health: `GET /health`
  - API docs: `GET /docs`

The service exposes Vanna’s v2 chat endpoints (`/api/vanna/v2/*`) for SSE, polling, and WebSocket.


### Notes on providers

- Anthropic: default when `LLM_PROVIDER` is unset or not `ollama`. Set `LLM_MODEL` to change model name.
- Ollama: ensure `OLLAMA_BASE_URL` points to a running server and that you’ve pulled a model. Default model name used is `OLLAMA_MODEL`.


### Project structure

```
app/
  __init__.py
  config.py          # .env configuration loader
  logging_config.py  # INFO level logging
  main.py            # FastAPI app (Vanna v2 server) and entrypoint
demo/
  postgres-demo.sql  # (optional) sample schema/data for Postgres
.env.example
pyproject.toml
README.md
```


### Troubleshooting

- If the server fails to start, ensure dependencies are installed (`uv sync`) and that your selected LLM provider is available.
- For Ollama, confirm the local server is running and the model is pulled.
- On Windows with corporate proxies, set `HTTP_PROXY`/`HTTPS_PROXY` as needed for dependency installs and provider access.


### License

MIT (or your preferred license).
