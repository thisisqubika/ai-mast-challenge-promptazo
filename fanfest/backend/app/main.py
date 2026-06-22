import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.endpoints import events
from app.core.config import settings
from app.db import database
from app.db import models as _models  # noqa: F401 — registers ORM classes with Base


def _run_migrations() -> None:
    """Add new columns to existing tables that predate them."""
    from sqlalchemy import text

    with database._engine.connect() as conn:
        for stmt in [
            "ALTER TABLE events ADD COLUMN recap_video_url TEXT",
        ]:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass  # column already exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    if database._engine is None:
        database.init_db(settings.database_url)
        _models.Base.metadata.create_all(database._engine)
        _run_migrations()
        from app.db.seed import run_seed
        run_seed()
    yield


app = FastAPI(title="FanFest API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve locally uploaded media files — must be mounted before routers
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(events.router, prefix="/api/v1")


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
