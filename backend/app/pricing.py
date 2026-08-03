"""
Price-response simulator + pricing optimiser.

Methodology (state explicitly in interviews and in the About page):
There is no experimental price-elasticity data in this dataset.  Instead the
system uses the *trained cancellation model itself* as a counterfactual demand
proxy: for a fixed booking context, sweep `adr` across a realistic range and
observe how predicted cancellation probability shifts.  This is a legitimate,
explainable technique (a form of partial-dependence / what-if analysis on a
trained supervised model).  Its limitation — it reflects correlational patterns
in historical cancellations, not true experimentally-measured demand elasticity
— should be stated up front.
"""
from __future__ import annotations

import numpy as np

from .inference import predict_cancellation_with_adr, get_metadata
from .features import _month_to_season


def get_base_price(market_segment: str, arrival_month: int) -> float:
    """
    Look up the segment × season average ADR from the precomputed table.

    Falls back to the global average if the combo is not found.
    """
    metadata = get_metadata()
    lut = metadata.get("segment_season_avg_adr", {})

    season = _month_to_season(arrival_month)
    key = f"{market_segment}_{season}"

    if key in lut:
        return lut[key]

    # fallback: mean of all entries, or global adr_mean
    if lut:
        return sum(lut.values()) / len(lut)
    return metadata.get("adr_mean", 100.0)


def simulate_price_response(
    booking_data: dict,
    price_grid: list[float],
) -> list[dict]:
    """
    Sweep ADR across ``price_grid`` and return ``[{price, p_cancel,
    expected_revenue}]``.  Each point is a full model evaluation with all
    adr-dependent features recomputed.
    """
    results = []
    for price in price_grid:
        p_cancel = predict_cancellation_with_adr(booking_data, price)
        results.append({
            "price":                    round(float(price), 2),
            "cancellation_probability": round(float(p_cancel), 4),
            "expected_revenue":         round(float(price * (1 - p_cancel)), 2),
        })
    return results


def recommend_price(booking_data: dict, occupancy_rate: float) -> dict:
    """
    Recommend a price that maximises expected revenue, subject to
    occupancy-pacing constraints.

    Parameters
    ----------
    booking_data : dict   — API-shaped booking (without ``adr``).
    occupancy_rate : float — current hotel occupancy in [0, 1].

    Returns
    -------
    dict with recommended_price, price_multiplier, expected_revenue,
    cancellation_probability_at_recommended_price, constraint_applied,
    price_curve.
    """
    arrival_month   = booking_data.get("arrival_month", 1)
    market_segment  = booking_data.get("market_segment", "Direct")
    lead_time       = booking_data.get("lead_time", 30)

    base_price = get_base_price(market_segment, arrival_month)

    # +/- 50% of base price, 25 points
    price_grid = np.linspace(0.7 * base_price, 1.5 * base_price, 25).tolist()

    curve = simulate_price_response(booking_data, price_grid)

    # ── occupancy-pacing constraints ────────────────────────────────────
    constraint = "normal pacing band"

    if occupancy_rate >= 0.85:
        filtered = [pt for pt in curve if pt["price"] >= base_price]
        constraint = "near-sellout: discount blocked"
    elif occupancy_rate <= 0.30 and lead_time <= 7:
        filtered = curve  # allow full discount range
        constraint = "low occupancy + last-minute: full range allowed"
    else:
        filtered = [
            pt for pt in curve
            if 0.85 * base_price <= pt["price"] <= 1.25 * base_price
        ]

    # fallback if filtering removed everything — preserve constraint intent
    if not filtered:
        if occupancy_rate >= 0.85:
            # Near-sellout: strictly enforce no discounting, even in fallback
            filtered = [pt for pt in curve if pt["price"] >= base_price]
            constraint += " (fallback: base price floor enforced)"
        else:
            filtered = curve
            constraint += " (fallback: full range)"

    # Ultimate fallback: if even the constraint-aware fallback is empty
    # (e.g. base_price is above entire grid), use the full curve
    if not filtered:
        filtered = curve
        constraint += " (ultimate fallback: full range)"

    best = max(filtered, key=lambda pt: pt["expected_revenue"])

    return {
        "recommended_price": best["price"],
        "price_multiplier":  round(best["price"] / base_price, 4) if base_price else 1.0,
        "expected_revenue":  best["expected_revenue"],
        "cancellation_probability_at_recommended_price": best["cancellation_probability"],
        "constraint_applied": constraint,
        "price_curve": curve,  # return the *full* curve for the chart
    }
