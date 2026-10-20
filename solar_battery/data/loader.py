"""Data loading and profile generation."""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Config (can be overridden)
BATTERY_CAPACITY_KWH = 13.5
BATTERY_MAX_POWER_KW = 5.0
BATTERY_EFFICIENCY = 0.95
INITIAL_SOC = 0.5
TOU_PRICES = True
REAL_DATA_PATH = Path(__file__).parent.parent.parent / "real_residential_sample.csv"


def generate_synthetic_profiles(hours: int = 72) -> pd.DataFrame:
    start = datetime(2026, 6, 15, 0, 0)
    timestamps = [start + timedelta(hours=i) for i in range(hours)]
    hours_of_day = np.array([t.hour for t in timestamps])
    solar = np.maximum(0, 5.5 * np.sin(np.pi * (hours_of_day - 6) / 12))
    solar[hours_of_day < 6] = 0
    solar[hours_of_day > 18] = 0
    solar *= np.random.uniform(0.75, 1.05, size=hours)
    load = 0.8 + 1.2 * np.sin(np.pi * (hours_of_day - 7) / 10) ** 2
    load += 0.4 * np.sin(np.pi * (hours_of_day - 18) / 6) ** 2
    load = np.clip(load, 0.3, 4.0) * np.random.uniform(0.9, 1.1, size=hours)
    price = _make_price(hours_of_day)
    return pd.DataFrame({
        "timestamp": timestamps,
        "solar_kw": np.round(solar, 3),
        "load_kw": np.round(load, 3),
        "price_per_kwh": price,
    })


def load_real_data(path: Path = REAL_DATA_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["utc_timestamp"])
    df["solar_kw"] = df["solar_kwh"].fillna(0)
    onsite = (df["solar_kwh"] - df["export_kwh"].fillna(0)).clip(lower=0)
    df["load_kw"] = df["load_kwh"].fillna(0) + onsite
    hours_of_day = df["timestamp"].dt.hour
    df["price_per_kwh"] = _make_price(hours_of_day)
    return df[["timestamp", "solar_kw", "load_kw", "price_per_kwh"]].copy()


def _make_price(hours_of_day):
    if TOU_PRICES:
        return np.where(
            (hours_of_day >= 16) & (hours_of_day <= 21), 0.35,
            np.where((hours_of_day >= 22) | (hours_of_day <= 6), 0.12, 0.18)
        )
    return np.full(len(hours_of_day), 0.18)
