import httpx
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from . import security
from .config import Settings, get_settings
from .db import connect, migrate
from .ddragon import DDragon, DDragonMissing, load, sync
from .puzzles.loader import Catalog, load_catalog
from .routes import auth, community, puzzles


def _load_ddragon(settings: Settings) -> DDragon:
    """Use the local cache; only touch the network when there is no cache yet (first boot)."""
    try:
        return load(settings.ddragon_dir)
    except DDragonMissing:
        pass
    try:
        with httpx.Client(timeout=30) as client:
            sync(settings.ddragon_dir, client)
        return load(settings.ddragon_dir)
    except (httpx.HTTPError, DDragonMissing) as e:
        raise RuntimeError(f"Data Dragon cache missing and sync failed: {e}. "
                           "Run `python -m app.admin sync-ddragon`") from e


def create_app(settings: Settings | None = None, dd: DDragon | None = None,
               catalog: Catalog | None = None) -> FastAPI:
    settings = settings or get_settings()
    conn = connect(settings.db_path)
    migrate(conn)
    conn.close()
    dd = dd or _load_ddragon(settings)
    catalog = catalog or load_catalog(settings.puzzles_dir, dd)

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.settings, app.state.dd, app.state.catalog = settings, dd, catalog
    security.install(app, settings.public_origin)

    @app.middleware("http")
    async def cache_headers(request: Request, call_next):
        response = await call_next(request)
        if response.status_code == 200:
            if request.url.path.startswith("/assets/"):  # Vite output, content-hashed names
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
            elif request.url.path.startswith("/dd/"):
                response.headers["Cache-Control"] = "public, max-age=86400"
        return response

    @app.get("/api/meta")
    def meta():
        return {"ddragon_version": dd.version}

    app.include_router(auth.router)
    app.include_router(puzzles.router)
    app.include_router(community.router)

    images = settings.ddragon_dir / "img"
    images.mkdir(parents=True, exist_ok=True)
    app.mount("/dd", StaticFiles(directory=images), name="dd")
    if settings.static_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.static_dir, html=True), name="static")
    return app
