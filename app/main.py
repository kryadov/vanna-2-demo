from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, render_template

from .api import api_bp
from .config import settings
from .logging_config import configure_logging
from .vanna_service import vanna_service


def create_app() -> Flask:
    configure_logging()
    logging.getLogger(__name__).info("Starting app with settings: %s", settings)

    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )

    # Blueprints
    app.register_blueprint(api_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    # Initialize Vanna lazily on first request (Flask 3 safe)
    app.config.setdefault("_VANNA_READY", False)

    @app.before_request
    def _ensure_vanna_ready():
        if not app.config.get("_VANNA_READY"):
            try:
                vanna_service.ensure_ready()
                app.config["_VANNA_READY"] = True
            except Exception as e:  # pragma: no cover
                logging.getLogger(__name__).error("Failed to initialize Vanna: %s", e)

    return app


def main() -> None:
    app = create_app()
    app.run(host=settings.app.host, port=settings.app.port, debug=settings.app.debug)


if __name__ == "__main__":
    main()
