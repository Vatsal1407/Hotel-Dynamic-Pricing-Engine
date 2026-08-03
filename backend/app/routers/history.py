"""History router — returns past pricing recommendations."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..schemas import HistoryItem
from ..db import get_db
from ..models import PricingRequest

router = APIRouter(tags=["history"])


@router.get("/history", response_model=List[HistoryItem])
def get_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(PricingRequest)
        .order_by(PricingRequest.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        HistoryItem(
            id=r.id,
            created_at=r.created_at.isoformat() if r.created_at else "",
            input_payload=r.input_payload or {},
            recommended_price=r.recommended_price,
            expected_revenue=r.expected_revenue,
            cancellation_probability=r.cancellation_probability,
            occupancy_rate=r.occupancy_rate,
        )
        for r in rows
    ]
