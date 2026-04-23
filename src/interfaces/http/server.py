from __future__ import annotations

from src.infrastructure.config.settings import load_settings
from src.interfaces.http.app_factory import create_app


if __name__ == "__main__":
    settings = load_settings()
    app = create_app()
    app.run(host=settings.flask_host, port=settings.flask_port)
