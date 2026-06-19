from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints import events
from app.core.config import settings

app = FastAPI(title="FanFest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(events.router, prefix="/api/v1")
