from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import events
from app.core.config import settings
from app.db import database
from app.db import models as _models  # noqa: F401 — registers ORM classes with Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    if database._engine is None:
        database.init_db(settings.database_url)
        _models.Base.metadata.create_all(database._engine)
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

app.include_router(events.router, prefix="/api/v1")


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
