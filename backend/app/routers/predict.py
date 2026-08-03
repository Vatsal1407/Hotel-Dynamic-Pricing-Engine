"""Prediction router — cancellation risk + price recommendation."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..schemas import (
    CancellationRiskRequest,
    CancellationRiskResponse,
    RecommendPriceRequest,
    RecommendPriceResponse,
    PriceCurvePoint,
)
from ..inference import predict_cancellation, get_threshold
from ..pricing import recommend_price
from ..db import get_db
from ..models import PricingRequest

router = APIRouter(prefix="/predict", tags=["predictions"])


def _risk_category(prob: float) -> str:
    """
    Classify risk using bands relative to the tuned decision threshold.
    Low  = well below threshold, High = well above, Medium = around it.
    """
    t = get_threshold()          # val-set-tuned threshold (e.g. ~0.35)
    if prob < t * 0.75:
        return "Low"
    if prob <= t * 1.5:
        return "Medium"
    return "High"


@router.post("/cancellation-risk", response_model=CancellationRiskResponse)
def cancellation_risk(request: CancellationRiskRequest):
    data = request.model_dump()
    p = predict_cancellation(data)
    return CancellationRiskResponse(
        cancellation_probability=round(p, 4),
        risk_category=_risk_category(p),
    )


@router.post("/recommend-price", response_model=RecommendPriceResponse)
def recommend_price_endpoint(
    request: RecommendPriceRequest,
    db: Session = Depends(get_db),
):
    data = request.model_dump()
    occupancy = data.pop("current_occupancy_rate")

    result = recommend_price(data, occupancy)

    # persist to DB for history dashboard
    record = PricingRequest(
        input_payload=data,
        recommended_price=result["recommended_price"],
        expected_revenue=result["expected_revenue"],
        cancellation_probability=result["cancellation_probability_at_recommended_price"],
        occupancy_rate=occupancy,
    )
    db.add(record)
    db.commit()

    return RecommendPriceResponse(
        recommended_price=round(result["recommended_price"], 2),
        price_multiplier=round(result["price_multiplier"], 4),
        expected_revenue=round(result["expected_revenue"], 2),
        cancellation_probability_at_recommended_price=round(
            result["cancellation_probability_at_recommended_price"], 4
        ),
        constraint_applied=result["constraint_applied"],
        price_curve=[
            PriceCurvePoint(**pt) for pt in result["price_curve"]
        ],
    )
