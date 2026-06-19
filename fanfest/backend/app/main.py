from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.endpoints.events import router as events_router

app = FastAPI(title="FanFest API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(events_router, prefix="/api/v1")


@app.get("/health")
def get_health() -> dict[str, str]:
    return {"status": "ok"}
