"""
Hotel Dynamic Pricing Engine — Backend API

A cancellation-risk-aware dynamic pricing recommender for small independent
hotels.  Uses an XGBoost cancellation model as a counterfactual demand proxy
to optimise expected revenue under occupancy-pacing constraints.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .db import engine, Base
from .inference import load_artifacts
from .routers import predict, history


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables (acceptable at this scale) and load model artifacts."""
    Base.metadata.create_all(bind=engine)
    load_artifacts()
    yield


app = FastAPI(
    title="Hotel Dynamic Pricing Engine",
    description=(
        "Cancellation-risk-aware dynamic pricing recommender for small "
        "independent hotels.  Uses an XGBoost cancellation model as a "
        "counterfactual demand proxy to optimise expected revenue under "
        "occupancy-pacing constraints."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(history.router)


@app.get("/health")
def health():
    return {"status": "ok"}
