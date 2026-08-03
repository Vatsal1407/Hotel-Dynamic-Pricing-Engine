"""
Data cleaning module for hotel booking data.

Cleaning rules are applied exactly as specified in the architecture document,
in the prescribed order.  The most critical step — dropping reservation_status
and reservation_status_date to prevent label leakage — is performed first.
"""
import pandas as pd
import numpy as np

# ---------- constants --------------------------------------------------------

MONTH_NAME_TO_NUM = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

NUMERIC_COLUMNS = [
    "lead_time", "arrival_date_year", "arrival_date_week_number",
    "arrival_date_day_of_month", "stays_in_weekend_nights",
    "stays_in_week_nights", "adults", "children", "babies",
    "is_repeated_guest", "previous_cancellations",
    "previous_bookings_not_canceled", "booking_changes",
    "days_in_waiting_list", "adr", "required_car_parking_spaces",
    "total_of_special_requests", "is_canceled",
]

CATEGORICAL_COLUMNS = [
    "hotel", "meal", "country", "market_segment",
    "distribution_channel", "reserved_room_type",
    "assigned_room_type", "deposit_type", "customer_type",
]

LEAK_COLUMNS = ["reservation_status", "reservation_status_date"]

# ---------- public API -------------------------------------------------------


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all cleaning rules from the architecture document.

    Returns a new DataFrame; the original is not modified.
    """
    df = df.copy()

    # Step 0 (critical): drop leaky columns immediately
    df = df.drop(
        columns=[c for c in LEAK_COLUMNS if c in df.columns],
        errors="ignore",
    )

    # Step 1: drop duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    after = len(df)
    if before != after:
        print(f"[clean] Dropped {before - after:,} duplicate rows")

    # Step 2: coerce numeric columns
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Step 3: clean categorical columns
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .replace(["nan", "None", "NaN"], "Unknown")
            )

    # Step 4: clip outliers
    df["lead_time"] = df["lead_time"].clip(0, 1000)
    df["adr"] = df["adr"].clip(10, 1000)

    # Extra: convert month names → integers (needed by feature engineering)
    # Use is_string_dtype to handle both object and pandas 3.0 StringDtype
    if "arrival_date_month" in df.columns and pd.api.types.is_string_dtype(df["arrival_date_month"]):
        df["arrival_date_month"] = (
            df["arrival_date_month"]
            .map(MONTH_NAME_TO_NUM)
            .fillna(1)
            .astype(int)
        )

    print(f"[clean] Cleaned dataset: {len(df):,} rows, {len(df.columns)} cols")
    return df
