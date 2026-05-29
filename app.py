from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, render_template, send_from_directory

from site_runtime import build_home_context


BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"


def create_app() -> Flask:
    load_dotenv(ENV_FILE)

    app = Flask(__name__, template_folder=str(BASE_DIR))
    app.config.from_mapping(
        GOOGLE_PLACES_API_KEY=_env_value("GOOGLE_PLACES_API_KEY", "GOOGLE_MAPS_API_KEY"),
        SELA_GOOGLE_PLACE_QUERY=(os.getenv("SELA_GOOGLE_PLACE_QUERY") or "Sela Construction Diamondhead MS").strip(),
        SELA_GOOGLE_PLACE_ID=_env_value("SELA_GOOGLE_PLACE_ID"),
    )

    @app.get("/")
    def home() -> str:
        return render_template(
            "home.html",
            **build_home_context(
                google_places_api_key=app.config["GOOGLE_PLACES_API_KEY"],
                google_place_query=app.config["SELA_GOOGLE_PLACE_QUERY"],
                google_place_id=app.config["SELA_GOOGLE_PLACE_ID"],
            ),
        )

    @app.get("/<path:filename>")
    def public_file(filename: str):
        if filename != "home.css" and not filename.startswith("assets/"):
            abort(404)
        return send_from_directory(BASE_DIR, filename)

    return app


def _env_value(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def main() -> None:
    app = create_app()
    host = (os.getenv("SELA_HOST") or "127.0.0.1").strip() or "127.0.0.1"
    port = int(os.getenv("SELA_PORT") or "5101")
    debug = (os.getenv("SELA_DEBUG") or "1").strip().lower() not in {"0", "false", "no"}
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()