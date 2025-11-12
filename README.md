### Vanna AI v2 — NL2SQL App (Flask + REST + Web UI)

This app is a minimal reference implementation that wires up Vanna AI v2 to a database (PostgreSQL or Oracle), exposes a REST API and a simple Web UI, and is configured via a `.env` file. It uses the `uv` Python package manager and runs on Python 3.13.

- REST API: `/api/health`, `/api/db-test`, `/api/ask`
- Web UI: `GET /` (simple form that calls `/api/ask`)
- Databases: PostgreSQL, Oracle (python-oracledb Thin)
- LLM providers: OpenAI, Google Generative AI, Ollama
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

- Database (choose one dialect)
  - `DB_DIALECT=postgres` or `DB_DIALECT=oracle`
  - Either set parts: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
  - Or provide a full DSN via `DB_DSN` which overrides parts

  Examples:
  - PostgreSQL: `postgresql+psycopg://user:pass@host:5432/dbname`
  - Oracle: `oracle+oracledb://user:pass@host:1521/?service_name=FREEPDB1`

- LLM provider (choose one)
  - `LLM_PROVIDER=openai | google | ollama`
  - OpenAI: `OPENAI_API_KEY`, optional `OPENAI_BASE_URL` (e.g., Azure or proxy)
  - Google GenAI: `GOOGLE_API_KEY`
  - Ollama: `OLLAMA_BASE_URL` (default `http://localhost:11434`) and optional `OLLAMA_MODEL` (default `llama3`)


### PostgreSQL demo schema (quick start)

If you want to try the app without hooking it up to your own database, a tiny demo schema with sample data is provided for PostgreSQL.

1) Ensure your `.env` points to a running Postgres instance and uses the `postgres` dialect, for example:
   ```ini
   DB_DIALECT=postgres
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=postgres
   DB_NAME=postgres
   ```

2) Load the demo schema and data using `psql`:
   - Windows (PowerShell):
     ```powershell
     psql -h $env:DB_HOST -p $env:DB_PORT -U $env:DB_USER -d $env:DB_NAME -f demo/postgres-demo.sql
     ```
     If you haven’t exported those env vars, just type them explicitly:
     ```powershell
     psql -h localhost -p 5432 -U postgres -d postgres -f demo/postgres-demo.sql
     ```
   - macOS/Linux:
     ```bash
     psql -h localhost -p 5432 -U postgres -d postgres -f demo/postgres-demo.sql
     ```

   Tip: If you’re using Docker for Postgres, you can run:
   ```bash
   docker exec -i <postgres-container> psql -U postgres -d postgres -f - < demo/postgres-demo.sql
   ```

3) Start the app (see “Running the app” below) and try questions like:
   - "Total revenue by customer in 2024"
   - "Top 5 products by revenue"
   - "Monthly revenue trend for 2024"
   - "List orders with their total amounts"

The demo creates tables: `categories`, `products`, `customers`, `orders`, `order_items` and helpful views: `order_revenue`, `customer_revenue_year`.


### Running the app

- Development server:
  ```powershell
  uv run vanna_app
  # or
  uv run python -m app.main
  ```

- Open in your browser: http://localhost:8000

- Health check and DB test:
  - `GET http://localhost:8000/api/health`
  - `GET http://localhost:8000/api/db-test`

- Ask endpoint:
  - `POST http://localhost:8000/api/ask`
    ```json
    {
      "question": "Top 10 customers by revenue in 2024",
      "execute": true,
      "limit": 50
    }
    ```

The service will generate SQL using Vanna and, if `execute=true`, it will run the SQL against your configured database. For safety, when a limit isn’t found in the query, the app wraps the generated SQL with a row cap (Postgres: `LIMIT N`, Oracle: `FETCH FIRST N ROWS ONLY`).


### Notes on providers

- OpenAI: requires `OPENAI_API_KEY`. If using Azure OpenAI or a proxy set `OPENAI_BASE_URL` accordingly.
- Google: requires `GOOGLE_API_KEY`. The app also calls `google.generativeai.configure(...)` when selected.
- Ollama: ensure `OLLAMA_BASE_URL` points to a running server and that you’ve pulled a model. Default model name used is `OLLAMA_MODEL`.


### Project structure

```
app/
  api.py             # REST endpoints
  config.py          # .env configuration loader
  db.py              # SQLAlchemy engine + helpers (Postgres/Oracle)
  logging_config.py  # INFO level logging
  main.py            # Flask app factory and entrypoint
  vanna_service.py   # Vanna v2 integration wrapper
  templates/
    index.html       # Web UI
  static/
    main.js          # UI logic to call /api/ask
    styles.css       # Basic styles
demo/
  postgres-demo.sql  # Sample retail schema and data for Postgres
.env.example
pyproject.toml
README.md
```


### Troubleshooting

- If Oracle connection fails, verify service name, port, and credentials. `python-oracledb` uses Thin mode by default and does not require Instant Client.
- If Vanna fails to initialize, try the force reinstall command above and confirm you’re on the `v2` branch.
- On Windows with corporate proxies, set `HTTP_PROXY`/`HTTPS_PROXY` as needed for dependency installs and provider access.


### License

MIT (or your preferred license).
