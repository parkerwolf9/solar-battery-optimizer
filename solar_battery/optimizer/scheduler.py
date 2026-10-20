"""Battery schedule optimizer."""
import pulp
import pandas as pd
from ..data.loader import (
    BATTERY_CAPACITY_KWH, BATTERY_MAX_POWER_KW,
    BATTERY_EFFICIENCY, INITIAL_SOC
)

# Tunable objective weights
EXPORT_PENALTY = 0.04          # $/kWh preference for on-site use
DEGRADATION_COST = 0.003       # $/kWh of battery throughput


def optimized_schedule(df: pd.DataFrame,
                       export_penalty: float = EXPORT_PENALTY,
                       degradation_cost: float = DEGRADATION_COST) -> pd.DataFrame:
    """Look-ahead LP minimizing grid cost + export penalty + degradation."""
    n = len(df)
    capacity = BATTERY_CAPACITY_KWH
    max_power = BATTERY_MAX_POWER_KW
    eff = BATTERY_EFFICIENCY

    solar = df["solar_kw"].values
    load = df["load_kw"].values
    price = df["price_per_kwh"].values

    m = pulp.LpProblem("solar_battery", pulp.LpMinimize)

    charge = [pulp.LpVariable(f"c_{t}", 0, max_power) for t in range(n)]
    discharge = [pulp.LpVariable(f"d_{t}", 0, max_power) for t in range(n)]
    g_imp = [pulp.LpVariable(f"gi_{t}", 0) for t in range(n)]
    g_exp = [pulp.LpVariable(f"ge_{t}", 0) for t in range(n)]
    soc = [pulp.LpVariable(f"soc_{t}", 0, capacity) for t in range(n + 1)]

    m += soc[0] == INITIAL_SOC * capacity

    # Objective: grid cost + export penalty + throughput degradation
    m += pulp.lpSum(
        g_imp[t] * price[t]
        + g_exp[t] * export_penalty
        + (charge[t] + discharge[t]) * degradation_cost
        for t in range(n)
    )

    for t in range(n):
        m += solar[t] + discharge[t] + g_imp[t] == load[t] + charge[t] + g_exp[t]
        m += soc[t + 1] == soc[t] + charge[t] * eff - discharge[t] / eff

    status = m.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        print(f"Warning: {pulp.LpStatus[status]}")

    rows = []
    for t in range(n):
        rows.append({
            "charge_kw": round(pulp.value(charge[t]) or 0, 3),
            "discharge_kw": round(pulp.value(discharge[t]) or 0, 3),
            "soc_kwh": round(pulp.value(soc[t + 1]) or 0, 3),
            "soc_pct": round(100 * (pulp.value(soc[t + 1]) or 0) / capacity, 1),
            "grid_import_kw": round(pulp.value(g_imp[t]) or 0, 3),
            "grid_export_kw": round(pulp.value(g_exp[t]) or 0, 3),
            "cost": round((pulp.value(g_imp[t]) or 0) * price[t], 3),
        })
    return df.join(pd.DataFrame(rows))


def simulate_schedule_on_actual(schedule_df: pd.DataFrame, actual_df: pd.DataFrame) -> pd.DataFrame:
    """Re-simulate forecast decisions against actual solar/load."""
    result = actual_df.copy()
    result["charge_kw"] = schedule_df["charge_kw"].values[:len(result)]
    result["discharge_kw"] = schedule_df["discharge_kw"].values[:len(result)]

    capacity = BATTERY_CAPACITY_KWH
    eff = BATTERY_EFFICIENCY
    soc = INITIAL_SOC * capacity
    rows = []
    for _, row in result.iterrows():
        charge = min(row["charge_kw"], BATTERY_MAX_POWER_KW, (capacity - soc) / eff)
        discharge = min(row["discharge_kw"], BATTERY_MAX_POWER_KW, soc * eff)
        soc = max(0.0, min(capacity, soc + charge * eff - discharge / eff))
        net = row["solar_kw"] - row["load_kw"] - charge + discharge
        rows.append({
            "charge_kw": round(charge, 3),
            "discharge_kw": round(discharge, 3),
            "soc_kwh": round(soc, 3),
            "soc_pct": round(100 * soc / capacity, 1),
            "grid_import_kw": round(max(0, -net), 3),
            "grid_export_kw": round(max(0, net), 3),
            "cost": round(max(0, -net) * row["price_per_kwh"], 3),
        })
    return result.drop(columns=["charge_kw", "discharge_kw"]).join(pd.DataFrame(rows))


def compute_metrics(df: pd.DataFrame) -> dict:
    total_solar = df["solar_kw"].sum()
    total_export = df["grid_export_kw"].sum()
    self_cons = (total_solar - total_export) / total_solar if total_solar > 0 else 0
    return {
        "total_load_kwh": round(df["load_kw"].sum(), 2),
        "total_solar_kwh": round(total_solar, 2),
        "total_grid_import_kwh": round(df["grid_import_kw"].sum(), 2),
        "total_grid_export_kwh": round(total_export, 2),
        "self_consumption_ratio": round(self_cons, 3),
        "total_cost_usd": round(df["cost"].sum(), 2),
        "avg_soc_pct": round(df["soc_pct"].mean(), 1),
    }
