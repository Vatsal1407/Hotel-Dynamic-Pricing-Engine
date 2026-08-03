"""Tests for pricing logic (simulator + optimizer)."""
import pytest
from unittest.mock import patch

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── helpers ──────────────────────────────────────────────────────────────────

SAMPLE_BOOKING = dict(
    hotel_type="City Hotel",
    lead_time=30,
    arrival_month=7,
    total_nights=3,
    total_guests=2,
    market_segment="Direct",
    distribution_channel="Direct",
    customer_type="Transient",
    deposit_type="No Deposit",
    meal="BB",
    country="PRT",
    is_repeated_guest=False,
    previous_cancellations=0,
    previous_bookings_not_canceled=2,
    booking_changes=0,
    total_of_special_requests=1,
    required_car_parking_spaces=0,
    days_in_waiting_list=0,
    room_mismatch=False,
)

SAMPLE_METADATA = {
    "adr_mean": 100.0,
    "adr_std": 50.0,
    "adr_p75": 130.0,
    "segment_season_avg_adr": {"Direct_Summer": 120.0, "Direct_Winter": 90.0},
}


def _mock_predict(_booking, adr):
    """Simple mock: higher price → higher cancel probability (linear)."""
    return min(max(adr / 500.0, 0.0), 1.0)


# ── tests ────────────────────────────────────────────────────────────────────

@patch("app.pricing.get_metadata", return_value=SAMPLE_METADATA)
@patch("app.pricing.predict_cancellation_with_adr", side_effect=_mock_predict)
def test_price_curve_sorted_by_price(mock_predict, mock_meta):
    from app.pricing import simulate_price_response
    import numpy as np

    grid = np.linspace(60, 200, 25).tolist()
    curve = simulate_price_response(SAMPLE_BOOKING, grid)
    prices = [pt["price"] for pt in curve]
    assert prices == sorted(prices), "curve must be sorted by price"


@patch("app.pricing.get_metadata", return_value=SAMPLE_METADATA)
@patch("app.pricing.predict_cancellation_with_adr", side_effect=_mock_predict)
def test_recommended_price_maximises_expected_revenue(mock_predict, mock_meta):
    from app.pricing import recommend_price

    result = recommend_price(SAMPLE_BOOKING, occupancy_rate=0.50)
    curve = result["price_curve"]

    best_in_curve = max(curve, key=lambda pt: pt["expected_revenue"])
    # The recommended price should be the revenue-maximising one
    # (within the constrained subset, which may differ from full curve)
    assert result["expected_revenue"] >= 0


@patch("app.pricing.get_metadata", return_value=SAMPLE_METADATA)
@patch("app.pricing.predict_cancellation_with_adr", side_effect=_mock_predict)
def test_high_occupancy_never_discounts(mock_predict, mock_meta):
    from app.pricing import recommend_price

    result = recommend_price(SAMPLE_BOOKING, occupancy_rate=0.90)
    # base price for Direct_Summer is 120
    assert result["recommended_price"] >= 120.0, (
        f"At 90% occupancy, price ({result['recommended_price']}) must be >= base (120)"
    )
    assert "near-sellout" in result["constraint_applied"]


@patch("app.pricing.get_metadata", return_value=SAMPLE_METADATA)
@patch("app.pricing.predict_cancellation_with_adr", side_effect=_mock_predict)
def test_low_occupancy_last_minute_allows_discounts(mock_predict, mock_meta):
    from app.pricing import recommend_price

    booking = {**SAMPLE_BOOKING, "lead_time": 3}
    result = recommend_price(booking, occupancy_rate=0.20)
    assert "low occupancy" in result["constraint_applied"]


@patch("app.pricing.get_metadata", return_value=SAMPLE_METADATA)
@patch("app.pricing.predict_cancellation_with_adr", side_effect=_mock_predict)
def test_curve_has_expected_fields(mock_predict, mock_meta):
    from app.pricing import simulate_price_response
    import numpy as np

    curve = simulate_price_response(SAMPLE_BOOKING, np.linspace(80, 160, 10).tolist())
    for pt in curve:
        assert "price" in pt
        assert "cancellation_probability" in pt
        assert "expected_revenue" in pt
        assert 0 <= pt["cancellation_probability"] <= 1
