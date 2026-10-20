"""Entry point for the solar + battery optimizer."""
from pathlib import Path
import sys

# Allow running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from solar_battery.data.loader import load_real_data, REAL_DATA_PATH
from solar_battery.forecast.forecast import hourly_average_forecast, persistence_forecast
from solar_battery.optimizer.scheduler import (
    optimized_schedule, simulate_schedule_on_actual, compute_metrics
)


def main():
    print("Loading real residential data...")
    actual = load_real_data()
    print(f"Loaded {len(actual)} hours\n")

    # Perfect foresight
    print("=== Perfect foresight ===")
    perfect = optimized_schedule(actual)
    m_perfect = compute_metrics(perfect)
    for k, v in m_perfect.items():
        print(f"  {k}: {v}")

    # Hourly-average forecast
    print("\n=== Hourly-average forecast (evaluated on actual) ===")
    avg_f = hourly_average_forecast(actual)
    avg_sched = optimized_schedule(avg_f)
    avg_eval = simulate_schedule_on_actual(avg_sched, actual)
    m_avg = compute_metrics(avg_eval)
    for k, v in m_avg.items():
        print(f"  {k}: {v}")

    # Persistence forecast
    print("\n=== Persistence forecast (previous day → next day) ===")
    pers_f = persistence_forecast(actual)
    pers_sched = optimized_schedule(pers_f)
    pers_eval = simulate_schedule_on_actual(pers_sched, actual)
    m_pers = compute_metrics(pers_eval)
    for k, v in m_pers.items():
        print(f"  {k}: {v}")

    print("\n--- Summary ---")
    print(f"Perfect foresight self-consumption: {m_perfect['self_consumption_ratio']:.3f}")
    print(f"Hourly-average forecast:            {m_avg['self_consumption_ratio']:.3f}")
    print(f"Persistence forecast:               {m_pers['self_consumption_ratio']:.3f}")

    out = Path(__file__).parent / "solar_battery_schedule.csv"
    perfect.to_csv(out, index=False)
    print(f"\nPerfect-foresight schedule saved to {out.name}")


if __name__ == "__main__":
    main()
