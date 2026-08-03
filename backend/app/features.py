"""
Feature engineering module — shared by training and inference.

Feature list (39 features):
  Temporal (8):  lead_time, lead_time_log, lead_time_squared, is_last_minute,
                 is_far_ahead, is_peak_season, arrival_date_month,
                 weekend_nights_ratio
  Guest (8):     total_nights, total_guests, is_repeated_guest,
                 previous_cancellations, previous_bookings_not_canceled,
                 loyalty_score, cancellation_rate_history, is_high_maintenance
  Pricing (4):   adr, adr_zscore, is_premium, revenue_per_guest_night
  Other (6):     room_mismatch, required_car_parking_spaces,
                 total_of_special_requests, days_in_waiting_list,
                 booking_changes, is_small_hotel
  Interactions (7): leadtime_x_adr, leadtime_x_changes, leadtime_x_nights,
                    guests_x_requests, adr_x_requests,
                    nonrefund_x_leadtime, repeat_cancel_nodeposit
  Encoded cats (6): deposit_type, meal, distribution_channel,
                    market_segment, customer_type, country
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# ── ordered list of the 39 output features ──────────────────────────────────

FEATURE_NAMES: list[str] = [
    # Temporal (8)
    "lead_time", "lead_time_log", "lead_time_squared",
    "is_last_minute", "is_far_ahead", "is_peak_season",
    "arrival_date_month", "weekend_nights_ratio",
    # Guest behaviour (8)
    "total_nights", "total_guests", "is_repeated_guest",
    "previous_cancellations", "previous_bookings_not_canceled",
    "loyalty_score", "cancellation_rate_history", "is_high_maintenance",
    # Pricing (4)
    "adr", "adr_zscore", "is_premium", "revenue_per_guest_night",
    # Other (6)
    "room_mismatch", "required_car_parking_spaces",
    "total_of_special_requests", "days_in_waiting_list",
    "booking_changes", "is_small_hotel",
    # Interactions (7)
    "leadtime_x_adr", "leadtime_x_changes", "leadtime_x_nights",
    "guests_x_requests", "adr_x_requests",
    "nonrefund_x_leadtime",       # NEW: Non-refund deposit × lead time
    "repeat_cancel_nodeposit",    # NEW: Repeat canceller with no deposit
    # Encoded categoricals (6)
    "deposit_type", "meal", "distribution_channel",
    "market_segment", "customer_type", "country",
]

# Columns that get LabelEncoded
CATEGORICAL_ENCODE_COLS: list[str] = [
    "deposit_type", "meal", "distribution_channel",
    "market_segment", "customer_type", "country",
]

# ── helpers ──────────────────────────────────────────────────────────────────


def _month_to_season(month) -> str:
    """Map month number (1-12) -> season name."""
    try:
        month = int(month)
    except (ValueError, TypeError):
        return "Spring"  # safe fallback
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    if month in (9, 10, 11):
        return "Fall"
    return "Spring"


# ── constants computed on training data ──────────────────────────────────────


def compute_feature_constants(df: pd.DataFrame) -> dict:
    """Compute adr_mean / adr_std / adr_p75 from the *training* split."""
    return {
        "adr_mean": float(df["adr"].mean()),
        "adr_std":  float(df["adr"].std()),
        "adr_p75":  float(df["adr"].quantile(0.75)),
    }


def compute_segment_season_avg_adr(df: pd.DataFrame) -> dict[str, float]:
    """
    Compute mean ADR grouped by market_segment x season.
    Used only to anchor the pricing optimizer's search range.
    """
    month_col = df["arrival_date_month"]
    seasons = month_col.map(_month_to_season)

    tmp = pd.DataFrame({
        "market_segment": df["market_segment"],
        "season": seasons,
        "adr": df["adr"],
    })
    grouped = tmp.groupby(["market_segment", "season"])["adr"].mean()
    return {f"{seg}_{ssn}": float(val) for (seg, ssn), val in grouped.items()}


# ── main feature-engineering function ────────────────────────────────────────


def engineer_features(
    df: pd.DataFrame,
    constants: dict,
    encoders: dict[str, LabelEncoder] | None = None,
    fit_encoders: bool = False,
) -> tuple[pd.DataFrame, dict[str, LabelEncoder] | None]:
    """
    Engineer the 39 features from cleaned booking data.

    Works for both training (full DataFrame) and inference (single-row DF).

    Parameters
    ----------
    df : pd.DataFrame
        Cleaned booking data.  Must contain the raw columns needed; the
        function tolerates both the training schema (with per-night columns)
        and the inference schema (with pre-aggregated ``total_nights`` etc.).
    constants : dict
        Must contain ``adr_mean``, ``adr_std``, ``adr_p75`` (floats).
    encoders : dict, optional
        Dict of *fitted* ``LabelEncoder`` objects keyed by column name.
        Required when ``fit_encoders`` is False.
    fit_encoders : bool
        If True, fit fresh encoders on ``df`` (training mode).

    Returns
    -------
    features_df : pd.DataFrame   -- exactly 39 columns in FEATURE_NAMES order.
    encoders    : dict            -- the (possibly newly-fitted) encoders.
    """
    out = pd.DataFrame(index=df.index)

    # ── derive base columns (handle both training & inference schemas) ──

    # total_nights
    if "total_nights" in df.columns:
        total_nights = df["total_nights"].clip(1, 365)
    else:
        total_nights = (
            df["stays_in_weekend_nights"] + df["stays_in_week_nights"]
        ).clip(1, 365)

    # total_guests
    if "total_guests" in df.columns:
        total_guests = df["total_guests"].clip(1, 10)
    else:
        total_guests = (
            df["adults"]
            + df.get("children", pd.Series(0, index=df.index))
            + df.get("babies", pd.Series(0, index=df.index))
        ).clip(1, 10)

    # room_mismatch
    if "room_mismatch" in df.columns:
        room_mismatch = df["room_mismatch"].astype(int)
    elif {"reserved_room_type", "assigned_room_type"}.issubset(df.columns):
        room_mismatch = (
            df["reserved_room_type"] != df["assigned_room_type"]
        ).astype(int)
    else:
        room_mismatch = pd.Series(0, index=df.index)

    # is_small_hotel
    if "is_small_hotel" in df.columns:
        is_small_hotel = df["is_small_hotel"].astype(int)
    elif "hotel" in df.columns:
        is_small_hotel = (df["hotel"] == "City Hotel").astype(int)
    elif "hotel_type" in df.columns:
        is_small_hotel = (df["hotel_type"] == "City Hotel").astype(int)
    else:
        is_small_hotel = pd.Series(0, index=df.index)

    # arrival_date_month (int 1-12)
    if "arrival_date_month" in df.columns:
        arrival_month = df["arrival_date_month"].astype(int)
    elif "arrival_month" in df.columns:
        arrival_month = df["arrival_month"].astype(int)
    else:
        arrival_month = pd.Series(1, index=df.index)

    # weekend_nights_ratio
    if "stays_in_weekend_nights" in df.columns:
        weekend_nights_ratio = (
            df["stays_in_weekend_nights"] / (total_nights + 0.001)
        )
    else:
        weekend_nights_ratio = pd.Series(0.0, index=df.index)

    adr = df["adr"]
    lead_time = df["lead_time"]

    # ── Raw deposit_type string (needed for interaction features BEFORE encoding)
    raw_deposit = df["deposit_type"].astype(str)
    is_nonrefund = (raw_deposit == "Non Refund").astype(int)

    # ── Temporal features (8) ───────────────────────────────────────────
    out["lead_time"]            = lead_time
    out["lead_time_log"]        = np.log1p(lead_time)
    out["lead_time_squared"]    = lead_time ** 2
    out["is_last_minute"]       = (lead_time <= 3).astype(int)
    out["is_far_ahead"]         = (lead_time > 365).astype(int)
    out["is_peak_season"]       = arrival_month.isin([6, 7, 8, 12]).astype(int)
    out["arrival_date_month"]   = arrival_month
    out["weekend_nights_ratio"] = weekend_nights_ratio

    # ── Guest behaviour features (8) ────────────────────────────────────
    out["total_nights"]                  = total_nights
    out["total_guests"]                  = total_guests
    out["is_repeated_guest"]             = df["is_repeated_guest"].astype(int)
    out["previous_cancellations"]        = df["previous_cancellations"]
    out["previous_bookings_not_canceled"] = df["previous_bookings_not_canceled"]
    out["loyalty_score"] = (
        df["is_repeated_guest"].astype(int) * 3
        + df["previous_bookings_not_canceled"] * 2
        - df["previous_cancellations"]
    )
    out["cancellation_rate_history"] = df["previous_cancellations"] / (
        df["previous_cancellations"] + df["previous_bookings_not_canceled"] + 1
    )
    out["is_high_maintenance"] = (
        (df["booking_changes"] > 2)
        | (df["total_of_special_requests"] > 3)
        | (df["days_in_waiting_list"] > 7)
    ).astype(int)

    # ── Pricing features (4) ───────────────────────────────────────────
    out["adr"]       = adr
    out["adr_zscore"] = (adr - constants["adr_mean"]) / (constants["adr_std"] + 0.001)
    out["is_premium"] = (adr > constants["adr_p75"]).astype(int)
    out["revenue_per_guest_night"] = adr / (total_guests + 0.001)

    # ── Other features (6) ─────────────────────────────────────────────
    out["room_mismatch"]              = room_mismatch
    out["required_car_parking_spaces"] = df["required_car_parking_spaces"]
    out["total_of_special_requests"]  = df["total_of_special_requests"]
    out["days_in_waiting_list"]       = df["days_in_waiting_list"]
    out["booking_changes"]            = df["booking_changes"]
    out["is_small_hotel"]             = is_small_hotel

    # ── Interaction features (7) ───────────────────────────────────────
    out["leadtime_x_adr"]     = lead_time * adr
    out["leadtime_x_changes"] = lead_time * df["booking_changes"]
    out["leadtime_x_nights"]  = lead_time * total_nights
    out["guests_x_requests"]  = total_guests * df["total_of_special_requests"]
    out["adr_x_requests"]     = adr * df["total_of_special_requests"]
    # NEW: Non-refundable deposit is a strong cancellation signal when combined
    # with long lead times (booked far ahead but no financial penalty to cancel)
    out["nonrefund_x_leadtime"] = is_nonrefund * lead_time
    # NEW: Repeat canceller with no-deposit booking — highest-risk combination
    out["repeat_cancel_nodeposit"] = (
        (df["previous_cancellations"] > 0) & (raw_deposit == "No Deposit")
    ).astype(int)

    # ── Encoded categoricals (6) ───────────────────────────────────────
    if fit_encoders:
        encoders = {}
        for col in CATEGORICAL_ENCODE_COLS:
            le = LabelEncoder()
            col_values = df[col].astype(str)
            # Ensure 'Unknown' is always a known class for inference safety
            all_values = list(col_values.unique())
            if "Unknown" not in all_values:
                all_values.append("Unknown")
            le.fit(all_values)
            out[col] = le.transform(col_values)
            encoders[col] = le
    else:
        if encoders is None:
            raise ValueError("encoders must be provided when fit_encoders=False")
        for col in CATEGORICAL_ENCODE_COLS:
            le = encoders[col]
            known = set(le.classes_)
            col_values = df[col].astype(str)
            # Map any unseen label to 'Unknown' (guaranteed in classes)
            fallback = "Unknown" if "Unknown" in known else le.classes_[0]
            out[col] = le.transform(
                [v if v in known else fallback for v in col_values]
            )

    # ── enforce column order ───────────────────────────────────────────
    out = out[FEATURE_NAMES]
    assert out.shape[1] == 39, f"Expected 39 features, got {out.shape[1]}"

    return out, encoders
