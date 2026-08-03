"""Pydantic request / response models for the API."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ── Cancellation Risk ────────────────────────────────────────────────────────

class CancellationRiskRequest(BaseModel):
    hotel_type: str = Field(..., pattern=r"^(Resort Hotel|City Hotel)$")
    lead_time: int
    arrival_month: int = Field(..., ge=1, le=12)
    total_nights: int
    total_guests: int
    market_segment: str
    distribution_channel: str
    customer_type: str
    deposit_type: str
    meal: str
    country: str
    adr: float
    is_repeated_guest: bool
    previous_cancellations: int
    previous_bookings_not_canceled: int
    booking_changes: int = 0
    total_of_special_requests: int = 0
    required_car_parking_spaces: int = 0
    days_in_waiting_list: int = 0
    room_mismatch: bool = False


class CancellationRiskResponse(BaseModel):
    cancellation_probability: float
    risk_category: str  # "Low" | "Medium" | "High"


# ── Price Recommendation ─────────────────────────────────────────────────────

class RecommendPriceRequest(BaseModel):
    hotel_type: str = Field(..., pattern=r"^(Resort Hotel|City Hotel)$")
    lead_time: int
    arrival_month: int = Field(..., ge=1, le=12)
    total_nights: int
    total_guests: int
    market_segment: str
    distribution_channel: str
    customer_type: str
    deposit_type: str
    meal: str
    country: str
    is_repeated_guest: bool
    previous_cancellations: int
    previous_bookings_not_canceled: int
    booking_changes: int = 0
    total_of_special_requests: int = 0
    required_car_parking_spaces: int = 0
    days_in_waiting_list: int = 0
    room_mismatch: bool = False
    current_occupancy_rate: float = Field(..., ge=0, le=1)


class PriceCurvePoint(BaseModel):
    price: float
    expected_revenue: float
    cancellation_probability: float


class RecommendPriceResponse(BaseModel):
    recommended_price: float
    price_multiplier: float
    expected_revenue: float
    cancellation_probability_at_recommended_price: float
    constraint_applied: str
    price_curve: List[PriceCurvePoint]


# ── History ──────────────────────────────────────────────────────────────────

class HistoryItem(BaseModel):
    id: int
    created_at: str
    input_payload: dict
    recommended_price: Optional[float] = None
    expected_revenue: Optional[float] = None
    cancellation_probability: Optional[float] = None
    occupancy_rate: Optional[float] = None
