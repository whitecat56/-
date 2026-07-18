from fastapi import FastAPI
from slowapi import Limiter
from slowapi.util import get_remote_address

from melody_ai.api.routers import auth, collections, music, users
from melody_ai.core.logging import configure_logging

configure_logging()
limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    app = FastAPI(
        title="MELODY AI API",
        version="1.0.0",
        description="Legal music metadata, previews, favorites, playlists and recommendations API",
    )
    app.state.limiter = limiter
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(music.router, prefix="/api/v1")
    app.include_router(collections.router, prefix="/api/v1")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
