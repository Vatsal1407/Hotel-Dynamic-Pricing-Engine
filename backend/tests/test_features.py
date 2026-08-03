"""Tests for the shared feature-engineering module."""
import numpy as np
import pandas as pd
import pytest
from sklearn.preprocessing import LabelEncoder

# We import from the backend copy of features.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.features import engineer_features, FEATURE_NAMES, CATEGORICAL_ENCODE_COLS

TEST_CONSTANTS = {"adr_mean": 100.0, "adr_std": 50.0, "adr_p75": 130.0}


def _make_encoders():
    """Build encoders with all labels the tests might use."""
    labels = {
        "deposit_type":         ["No Deposit", "Refundable", "Non Refund", "Unknown"],
        "meal":                 ["BB", "HB", "FB", "SC", "Undefined", "Unknown"],
        "distribution_channel": ["Direct", "Corporate", "TA/TO", "Unknown"],
        "market_segment":       ["Direct", "Corporate", "Online TA", "Offline TA/TO", "Unknown"],
        "customer_type":        ["Transient", "Contract", "Transient-Party", "Group", "Unknown"],
        "country":              ["PRT", "GBR", "USA", "ESP", "FRA", "DEU", "Unknown"],
    }
    encs = {}
    for col in CATEGORICAL_ENCODE_COLS:
        le = LabelEncoder()
        le.fit(labels[col])
        encs[col] = le
    return encs


def _row(**overrides):
    """Return a one-row DataFrame with sensible defaults."""
    base = dict(
        lead_time=30, arrival_date_month=7,
        stays_in_weekend_nights=2, stays_in_week_nights=3,
        adults=2, children=1, babies=0,
        is_repeated_guest=0, previous_cancellations=1,
        previous_bookings_not_canceled=3, booking_changes=1,
        total_of_special_requests=2, days_in_waiting_list=0,
        adr=120.0, required_car_parking_spaces=1,
        reserved_room_type="A", assigned_room_type="A",
        hotel="City Hotel",
        deposit_type="No Deposit", meal="BB",
        distribution_channel="Direct", market_segment="Direct",
        customer_type="Transient", country="PRT",
    )
    base.update(overrides)
    return pd.DataFrame([base])


@pytest.fixture
def encoders():
    return _make_encoders()


# ── shape & naming ───────────────────────────────────────────────────────────

def test_produces_39_features(encoders):
    feats, _ = engineer_features(_row(), TEST_CONSTANTS, encoders=encoders)
    assert feats.shape[1] == 39, f"got {feats.shape[1]}"


def test_column_order_matches_feature_names(encoders):
    feats, _ = engineer_features(_row(), TEST_CONSTANTS, encoders=encoders)
    assert list(feats.columns) == FEATURE_NAMES


# ── temporal ─────────────────────────────────────────────────────────────────

def test_lead_time_log(encoders):
    feats, _ = engineer_features(_row(), TEST_CONSTANTS, encoders=encoders)
    assert abs(feats["lead_time_log"].iloc[0] - np.log1p(30)) < 1e-6


def test_lead_time_squared(encoders):
    feats, _ = engineer_features(_row(), TEST_CONSTANTS, encoders=encoders)
    assert feats["lead_time_squared"].iloc[0] == 30 ** 2


def test_is_last_minute_true(encoders):
    feats, _ = engineer_features(_row(lead_time=2), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_last_minute"].iloc[0] == 1


def test_is_last_minute_false(encoders):
    feats, _ = engineer_features(_row(lead_time=30), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_last_minute"].iloc[0] == 0


def test_is_far_ahead(encoders):
    feats, _ = engineer_features(_row(lead_time=400), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_far_ahead"].iloc[0] == 1


def test_peak_season_july(encoders):
    feats, _ = engineer_features(_row(arrival_date_month=7), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_peak_season"].iloc[0] == 1


def test_not_peak_season_march(encoders):
    feats, _ = engineer_features(_row(arrival_date_month=3), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_peak_season"].iloc[0] == 0


# ── guest behaviour ──────────────────────────────────────────────────────────

def test_total_nights(encoders):
    feats, _ = engineer_features(
        _row(stays_in_weekend_nights=2, stays_in_week_nights=3),
        TEST_CONSTANTS, encoders=encoders,
    )
    assert feats["total_nights"].iloc[0] == 5


def test_loyalty_score(encoders):
    feats, _ = engineer_features(
        _row(is_repeated_guest=1, previous_bookings_not_canceled=5, previous_cancellations=2),
        TEST_CONSTANTS, encoders=encoders,
    )
    # 1*3 + 5*2 - 2 = 11
    assert feats["loyalty_score"].iloc[0] == 11


def test_cancellation_rate_history(encoders):
    feats, _ = engineer_features(
        _row(previous_cancellations=2, previous_bookings_not_canceled=3),
        TEST_CONSTANTS, encoders=encoders,
    )
    expected = 2 / (2 + 3 + 1)
    assert abs(feats["cancellation_rate_history"].iloc[0] - expected) < 1e-6


def test_is_high_maintenance(encoders):
    feats, _ = engineer_features(
        _row(booking_changes=5, total_of_special_requests=1, days_in_waiting_list=0),
        TEST_CONSTANTS, encoders=encoders,
    )
    assert feats["is_high_maintenance"].iloc[0] == 1


# ── pricing ──────────────────────────────────────────────────────────────────

def test_adr_zscore(encoders):
    feats, _ = engineer_features(_row(adr=120.0), TEST_CONSTANTS, encoders=encoders)
    expected = (120.0 - 100.0) / (50.0 + 0.001)
    assert abs(feats["adr_zscore"].iloc[0] - expected) < 1e-4


def test_is_premium_true(encoders):
    feats, _ = engineer_features(_row(adr=150.0), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_premium"].iloc[0] == 1  # 150 > 130


def test_is_premium_false(encoders):
    feats, _ = engineer_features(_row(adr=100.0), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_premium"].iloc[0] == 0  # 100 < 130


# ── other ────────────────────────────────────────────────────────────────────

def test_room_mismatch_yes(encoders):
    feats, _ = engineer_features(
        _row(reserved_room_type="A", assigned_room_type="B"),
        TEST_CONSTANTS, encoders=encoders,
    )
    assert feats["room_mismatch"].iloc[0] == 1


def test_room_mismatch_no(encoders):
    feats, _ = engineer_features(
        _row(reserved_room_type="A", assigned_room_type="A"),
        TEST_CONSTANTS, encoders=encoders,
    )
    assert feats["room_mismatch"].iloc[0] == 0


def test_is_small_hotel_city(encoders):
    feats, _ = engineer_features(_row(hotel="City Hotel"), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_small_hotel"].iloc[0] == 1


def test_is_small_hotel_resort(encoders):
    feats, _ = engineer_features(_row(hotel="Resort Hotel"), TEST_CONSTANTS, encoders=encoders)
    assert feats["is_small_hotel"].iloc[0] == 0


# ── interactions ─────────────────────────────────────────────────────────────

def test_leadtime_x_adr(encoders):
    feats, _ = engineer_features(_row(lead_time=30, adr=120.0), TEST_CONSTANTS, encoders=encoders)
    assert feats["leadtime_x_adr"].iloc[0] == 30 * 120.0


def test_nonrefund_x_leadtime_active(encoders):
    """Non-refundable deposit + long lead time -> high interaction value."""
    feats, _ = engineer_features(
        _row(deposit_type="Non Refund", lead_time=90), TEST_CONSTANTS, encoders=encoders
    )
    assert feats["nonrefund_x_leadtime"].iloc[0] == 90


def test_nonrefund_x_leadtime_inactive(encoders):
    """No-deposit booking -> interaction is zero regardless of lead time."""
    feats, _ = engineer_features(
        _row(deposit_type="No Deposit", lead_time=90), TEST_CONSTANTS, encoders=encoders
    )
    assert feats["nonrefund_x_leadtime"].iloc[0] == 0


def test_repeat_cancel_nodeposit_high_risk(encoders):
    """Repeat canceller + no deposit -> flag is 1."""
    feats, _ = engineer_features(
        _row(deposit_type="No Deposit", previous_cancellations=2),
        TEST_CONSTANTS, encoders=encoders,
    )
    assert feats["repeat_cancel_nodeposit"].iloc[0] == 1


def test_repeat_cancel_nodeposit_no_history(encoders):
    """First-time booker + no deposit -> flag is 0."""
    feats, _ = engineer_features(
        _row(deposit_type="No Deposit", previous_cancellations=0),
        TEST_CONSTANTS, encoders=encoders,
    )
    assert feats["repeat_cancel_nodeposit"].iloc[0] == 0
