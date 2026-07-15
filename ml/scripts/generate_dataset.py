"""
generate_dataset.py
--------------------
Generates a realistic synthetic dataset for training the irrigation
prediction model. The physical relationships are hand-crafted to mimic
real agronomic rules of thumb:

  - Low soil moisture + high temperature + low humidity  -> irrigate, more water
  - High soil moisture                                    -> do not irrigate
  - Rain-like humidity (very high) reduces water need even if moisture is low

Columns:
  soil_moisture (%)   0-100   (lower = drier)
  temperature   (°C)  10-45
  humidity      (%)   10-100
  irrigate      (0/1) target classification label
  water_amount_l (float) target regression label (liters, 0 if irrigate=0)
"""

import numpy as np
import pandas as pd
import os

RANDOM_SEED = 42
N_SAMPLES = 4000

np.random.seed(RANDOM_SEED)


def simulate_row():
    soil_moisture = np.clip(np.random.normal(45, 20), 0, 100)
    temperature = np.clip(np.random.normal(27, 7), 10, 45)
    humidity = np.clip(np.random.normal(55, 20), 10, 100)

    # Agronomic scoring heuristic (irrigation need score)
    dryness_score = (100 - soil_moisture) / 100          # higher = drier
    heat_score = (temperature - 10) / 35                  # higher = hotter
    dry_air_score = (100 - humidity) / 100                 # higher = drier air

    need_score = (0.55 * dryness_score) + (0.25 * heat_score) + (0.20 * dry_air_score)
    need_score += np.random.normal(0, 0.05)  # sensor/environmental noise

    irrigate = 1 if need_score > 0.45 else 0

    if irrigate:
        # Water amount scales with need_score, capped realistically for a small plot (liters)
        water_amount_l = round(float(np.clip(need_score * 40 + np.random.normal(0, 2), 2, 50)), 2)
    else:
        water_amount_l = 0.0

    return soil_moisture, temperature, humidity, irrigate, water_amount_l


def main():
    rows = [simulate_row() for _ in range(N_SAMPLES)]
    df = pd.DataFrame(
        rows,
        columns=["soil_moisture", "temperature", "humidity", "irrigate", "water_amount_l"],
    )
    df["soil_moisture"] = df["soil_moisture"].round(2)
    df["temperature"] = df["temperature"].round(2)
    df["humidity"] = df["humidity"].round(2)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "irrigation_dataset.csv")
    df.to_csv(out_path, index=False)

    print(f"Generated {len(df)} rows -> {out_path}")
    print(df["irrigate"].value_counts(normalize=True))


if __name__ == "__main__":
    main()
