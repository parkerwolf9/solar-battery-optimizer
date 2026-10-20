"""Forecasting utilities."""
import numpy as np
import pandas as pd


def hourly_average_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """Average by hour-of-day (baseline)."""
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    avg = df.groupby("hour")[["solar_kw", "load_kw"]].mean().reset_index()
    n_days = max(1, len(df) // 24)
    rows = []
    start = df["timestamp"].iloc[0]
    for day in range(n_days):
        for _, r in avg.iterrows():
            rows.append({
                "timestamp": start + pd.Timedelta(days=day, hours=int(r["hour"])),
                "solar_kw": r["solar_kw"],
                "load_kw": r["load_kw"],
            })
    f = pd.DataFrame(rows)
    f["price_per_kwh"] = _price_from_hour(f["timestamp"].dt.hour)
    return f[["timestamp", "solar_kw", "load_kw", "price_per_kwh"]]


def persistence_forecast(df: pd.DataFrame) -> pd.DataFrame:
    """Use the previous day's profile as the forecast for the next day (shifted)."""
    df = df.copy().sort_values("timestamp").reset_index(drop=True)
    if len(df) < 48:
        return hourly_average_forecast(df)
    # Shift by 24 hours
    shifted = df[["solar_kw", "load_kw"]].shift(24)
    forecast = df.copy()
    forecast["solar_kw"] = shifted["solar_kw"].fillna(df["solar_kw"])
    forecast["load_kw"] = shifted["load_kw"].fillna(df["load_kw"])
    return forecast[["timestamp", "solar_kw", "load_kw", "price_per_kwh"]]


def _price_from_hour(hours):
    return np.where(
        (hours >= 16) & (hours <= 21), 0.35,
        np.where((hours >= 22) | (hours <= 6), 0.12, 0.18)
    )
