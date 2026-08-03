"""API integration tests using FastAPI TestClient."""
import os
import sys

# Set test DATABASE_URL to SQLite before any app imports
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["MODEL_ARTIFACT_PATH"] = "./artifacts"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch, MagicMock

# ── mock artifacts before importing app ──────────────────────────────────────

MOCK_METADATA = {
    "adr_mean": 100.0,
    "adr_std": 50.0,
    "adr_p75": 130.0,
    "segment_season_avg_adr": {"Direct_Summer": 120.0},
}


def _mock_predict(data):
    return 0.35


def _mock_predict_adr(data, adr):
    return min(max(adr / 500.0, 0.0), 1.0)


# Patch load_artifacts before the app lifespan tries to call it
@pytest.fixture()
def client():
    """Create TestClient with mocked model inference."""
    with patch("app.inference.load_artifacts"), \
         patch("app.inference._model", MagicMock()), \
         patch("app.inference._encoders", MagicMock()), \
         patch("app.inference._constants", {"adr_mean": 100.0, "adr_std": 50.0, "adr_p75": 130.0}), \
         patch("app.inference._threshold", 0.35), \
         patch("app.inference._metadata", MOCK_METADATA), \
         patch("app.inference.predict_cancellation", side_effect=_mock_predict), \
         patch("app.inference.predict_cancellation_with_adr", side_effect=_mock_predict_adr), \
         patch("app.inference.get_metadata", return_value=MOCK_METADATA), \
         patch("app.pricing.predict_cancellation_with_adr", side_effect=_mock_predict_adr), \
         patch("app.pricing.get_metadata", return_value=MOCK_METADATA):

        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as c:
            yield c


# ── valid booking payload ────────────────────────────────────────────────────

VALID_BOOKING = dict(
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
)


# ── health ───────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ── cancellation risk ────────────────────────────────────────────────────────

def test_cancellation_risk_valid(client):
    payload = {**VALID_BOOKING, "adr": 120.0}
    r = client.post("/predict/cancellation-risk", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "cancellation_probability" in body
    assert "risk_category" in body
    assert body["risk_category"] in ("Low", "Medium", "High")


def test_cancellation_risk_invalid_hotel(client):
    payload = {**VALID_BOOKING, "adr": 120.0, "hotel_type": "Invalid"}
    r = client.post("/predict/cancellation-risk", json=payload)
    assert r.status_code == 422


def test_cancellation_risk_missing_field(client):
    payload = {**VALID_BOOKING}
    # missing 'adr' which is required
    r = client.post("/predict/cancellation-risk", json=payload)
    assert r.status_code == 422


# ── recommend price ──────────────────────────────────────────────────────────

def test_recommend_price_valid(client):
    payload = {**VALID_BOOKING, "current_occupancy_rate": 0.50}
    r = client.post("/predict/recommend-price", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "recommended_price" in body
    assert "price_multiplier" in body
    assert "expected_revenue" in body
    assert "price_curve" in body
    assert "constraint_applied" in body
    assert len(body["price_curve"]) > 0


def test_recommend_price_invalid_occupancy(client):
    payload = {**VALID_BOOKING, "current_occupancy_rate": 1.5}
    r = client.post("/predict/recommend-price", json=payload)
    assert r.status_code == 422


# ── history ──────────────────────────────────────────────────────────────────

def test_history_returns_list(client):
    r = client.get("/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
