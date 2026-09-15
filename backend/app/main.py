from fastapi import FastAPI

from app.api.ingestion import router as ingestion_router
from app.api.rules import findings_router, router as rules_router
from app.api.execution_gap import router as execution_gap_router
from app.api.negative_space import router as negative_space_router
from app.api.peer_anomaly import router as peer_anomaly_router
from app.api.supervisory_risk import router as supervisory_risk_router
from app.config import settings

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ingestion_router)
app.include_router(rules_router)
app.include_router(findings_router)
app.include_router(execution_gap_router)
app.include_router(negative_space_router)
app.include_router(peer_anomaly_router)
app.include_router(supervisory_risk_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "SAT-SA API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "sat-sa",
        "environment": settings.environment,
    }