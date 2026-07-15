"""
train_model.py
---------------
Trains two models on the irrigation dataset:

  1. RandomForestClassifier  -> irrigate (YES/NO)
  2. RandomForestRegressor   -> water_amount_l (liters to apply, only meaningful if irrigate=YES)

Both models + a shared StandardScaler are bundled into a single
.pkl artifact via joblib so the backend only needs to load one file.

Usage:
    python train_model.py
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    mean_absolute_error,
    r2_score,
)

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "irrigation_dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "irrigation_model.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")

FEATURES = ["soil_moisture", "temperature", "humidity"]


def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Dataset not found at {DATA_PATH}. Run generate_dataset.py first."
        )

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURES].values
    y_class = df["irrigate"].values
    y_reg = df["water_amount_l"].values

    X_train, X_test, yc_train, yc_test, yr_train, yr_test = train_test_split(
        X, y_class, y_reg, test_size=0.2, random_state=42, stratify=y_class
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    clf = RandomForestClassifier(
        n_estimators=200, max_depth=8, random_state=42, class_weight="balanced"
    )
    clf.fit(X_train_scaled, yc_train)

    # Regressor only trained on rows where irrigation actually happens
    reg_mask_train = yc_train == 1
    reg = RandomForestRegressor(n_estimators=200, max_depth=8, random_state=42)
    reg.fit(X_train_scaled[reg_mask_train], yr_train[reg_mask_train])

    # ---- Evaluation ----
    yc_pred = clf.predict(X_test_scaled)
    acc = accuracy_score(yc_test, yc_pred)
    prec = precision_score(yc_test, yc_pred)
    rec = recall_score(yc_test, yc_pred)
    f1 = f1_score(yc_test, yc_pred)

    reg_mask_test = yc_test == 1
    yr_pred = reg.predict(X_test_scaled[reg_mask_test])
    mae = mean_absolute_error(yr_test[reg_mask_test], yr_pred)
    r2 = r2_score(yr_test[reg_mask_test], yr_pred)

    metrics = {
        "classifier": {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1},
        "regressor": {"mae_liters": mae, "r2": r2},
        "n_train": len(X_train),
        "n_test": len(X_test),
        "features": FEATURES,
    }

    print("=== Classifier metrics ===")
    print(json.dumps(metrics["classifier"], indent=2))
    print("=== Regressor metrics (water amount, liters) ===")
    print(json.dumps(metrics["regressor"], indent=2))

    os.makedirs(MODEL_DIR, exist_ok=True)
    bundle = {
        "classifier": clf,
        "regressor": reg,
        "scaler": scaler,
        "features": FEATURES,
    }
    joblib.dump(bundle, MODEL_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved model bundle -> {MODEL_PATH}")
    print(f"Saved metrics       -> {METRICS_PATH}")


if __name__ == "__main__":
    main()
