# Residential Solar + Battery Schedule Optimizer

A small, public project that applies look-ahead optimization and simple forecasting to real residential solar + storage data. Built to bridge software/AI skills into the physical constraint of usable energy throughput.

## Why this project

Once the solar → robots → chips → AI loop closes, the scarce resources are wattage and tonnage, not software. This project shows how to take real household solar and load data, reconstruct total consumption, and schedule a battery with a linear program that sees the full horizon. It also demonstrates the gap between perfect foresight and realistic forecasts.

## Quick start

```bash
git clone https://github.com/parkerwolf9/solar-battery-optimizer.git
cd solar-battery-optimizer
pip install -r requirements.txt
python -m solar_battery.main
```

## What it does

1. Loads a 7-day sample of real residential data (Open Power System Data, household DE_KN_residential4, July 2016).
2. Reconstructs total household load as `grid_import + (solar − export)`.
3. Solves a look-ahead linear program that minimizes:
   - grid import cost
   - export penalty (encourages self-consumption)
   - battery degradation cost (throughput)
4. Compares three modes:
   - Perfect foresight
   - Hourly-average forecast
   - Persistence forecast (previous day used for next day)

## Results (7-day sample)

| Mode | Self-consumption | Grid import | Cost |
|------|------------------|-------------|------|
| Perfect foresight | ~28% | 0 | $0 |
| Hourly-average forecast | ~25% | ~9 kWh | ~$2.50 |
| Persistence forecast | ~25% | ~7 kWh | ~$1.90 |

On this high-solar week the house generated ~246 kWh and used only ~62 kWh. Even with the battery shifting energy, self-consumption is near the physical ceiling set by the load-to-solar ratio. The forecast gap is still visible but smaller.

## Project structure

```
solar_battery/
├── data/loader.py          # synthetic + real data loading
├── forecast/forecast.py    # hourly average + persistence
├── optimizer/scheduler.py  # PuLP LP + metrics
├── main.py                 # entry point
├── real_residential_sample.csv
└── requirements.txt
```

## Data attribution

Household solar and load sample from Open Power System Data (2020).  
Data Package Household Data, version 2020-04-15.  
https://data.open-power-system-data.org/household_data/2020-04-15/  
Licensed under Creative Commons Attribution (CC-BY).

## Next extensions

- Weather-driven solar forecast
- Multi-day rolling horizon
- Real home telemetry (if you install solar + storage)
