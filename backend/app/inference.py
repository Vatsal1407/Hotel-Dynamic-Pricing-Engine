"""
Model inference module.

Loads trained artifacts at startup and exposes ``predict_cancellation()`` and
``predict_cancellation_with_adr()`` for the pricing simulator.

Changes:
  - StandardScaler removed (XGBoost is scale-invariant).
  - Decision threshold loaded from feature_metadata_v1.json and applied in
    predict_cancellation(); raw probability still returned for the API.
"""
from __future__ import annotations

import os
import json

import joblib
import numpy as np
import pandas as pd

from .config import MODEL_ARTIFACT_PATH
from .features import engineer_features, FEATURE_NAMES

# ── global singletons (loaded once at startup) ──────────────────────────────

_model    = None
_encoders = None
_constants: dict | None = None
_metadata:  dict | None = None
_threshold: float = 0.5   # default; overridden by artifact value


def load_artifacts() -> None:
    """Load all model artifacts.  Called once via the FastAPI lifespan hook."""
    global _model, _encoders, _constants, _metadata, _threshold

    d = MODEL_ARTIFACT_PATH
    _model    = joblib.load(os.path.join(d, "model_v1.joblib"))
    _encoders = joblib.load(os.path.join(d, "encoders_v1.joblib"))

    with open(os.path.join(d, "feature_metadata_v1.json")) as f:
        _metadata = json.load(f)

    _constants = {
        "adr_mean": _metadata["adr_mean"],
        "adr_std":  _metadata["adr_std"],
        "adr_p75":  _metadata["adr_p75"],
    }
    # Load the val-set-tuned threshold (falls back to 0.5 for old artifacts)
    _threshold = float(_metadata.get("best_threshold", 0.5))

    print(f"[inference] Artifacts loaded from {d}")
    print(f"[inference] Decision threshold: {_threshold:.3f}")


# ── accessors ────────────────────────────────────────────────────────────────

def get_model():      return _model
def get_encoders():   return _encoders
def get_constants():  return _constants
def get_metadata():   return _metadata
def get_threshold():  return _threshold


# ── helpers ──────────────────────────────────────────────────────────────────


def booking_to_dataframe(booking_data: dict) -> pd.DataFrame:
    """Convert an API-shaped booking dict into a one-row DataFrame."""
    row = {
        "lead_time":                    booking_data["lead_time"],
        "arrival_date_month":           booking_data["arrival_month"],
        "total_nights":                 booking_data["total_nights"],
        "total_guests":                 booking_data["total_guests"],
        "market_segment":               booking_data["market_segment"],
        "distribution_channel":         booking_data["distribution_channel"],
        "customer_type":                booking_data["customer_type"],
        "deposit_type":                 booking_data["deposit_type"],
        "meal":                         booking_data["meal"],
        "country":                      booking_data["country"],
        "adr":                          booking_data["adr"],
        "is_repeated_guest":            int(booking_data["is_repeated_guest"]),
        "previous_cancellations":       booking_data["previous_cancellations"],
        "previous_bookings_not_canceled": booking_data["previous_bookings_not_canceled"],
        "booking_changes":              booking_data.get("booking_changes", 0),
        "total_of_special_requests":    booking_data.get("total_of_special_requests", 0),
        "required_car_parking_spaces":  booking_data.get("required_car_parking_spaces", 0),
        "days_in_waiting_list":         booking_data.get("days_in_waiting_list", 0),
        "room_mismatch":                int(booking_data.get("room_mismatch", False)),
        "hotel_type":                   booking_data["hotel_type"],
    }
    return pd.DataFrame([row])


# ── prediction API ───────────────────────────────────────────────────────────


def predict_cancellation(booking_data: dict) -> float:
    """
    Predict cancellation probability for a single booking.

    Returns the raw probability (not thresholded) so the API layer can display
    the continuous value; the threshold is used by the risk_category label.

    Parameters
    ----------
    booking_data : dict
        Booking fields matching the API request schema.

    Returns
    -------
    float -- cancellation probability in [0, 1].
    """
    df = booking_to_dataframe(booking_data)
    # No scaling -- XGBoost is tree-based and scale-invariant
    features, _ = engineer_features(df, _constants, encoders=_encoders)
    X = features.values
    return float(_model.predict_proba(X)[:, 1][0])


def predict_cancellation_with_adr(booking_data: dict, adr: float) -> float:
    """
    Predict cancellation probability at a *counterfactual* ADR value.

    Used by the pricing simulator when sweeping the price grid.
    All adr-dependent features are recomputed inside ``engineer_features``
    because the incoming ``adr`` field is overwritten before engineering.
    """
    modified = {**booking_data, "adr": adr}
    return predict_cancellation(modified)
