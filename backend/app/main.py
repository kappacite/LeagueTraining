from fastapi import FastAPI

from . import security
from .config import Settings, get_settings
from .db import connect, migrate
from .ddragon import DDragon, load
from .puzzles.loader import Catalog, load_catalog
from .routes import auth, puzzles


def create_app(settings: Settings | None = None, dd: DDragon | None = None,
               catalog: Catalog | None = None) -> FastAPI:
    settings = settings or get_settings()
    conn = connect(settings.db_path)
    migrate(conn)
    conn.close()
    dd = dd or load(settings.ddragon_dir)
    catalog = catalog or load_catalog(settings.puzzles_dir, dd)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings, app.state.dd, app.state.catalog = settings, dd, catalog
    security.install(app, settings.public_origin)
    app.include_router(auth.router)
    app.include_router(puzzles.router)
    return app
