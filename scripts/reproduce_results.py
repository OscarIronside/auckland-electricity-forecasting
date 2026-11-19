"""Reproduce the notebook's selected model and score the separate app export.

Run from any directory with Python, numpy, pandas and scikit-learn installed.
This script reads the committed daily data; no raw download or API key is needed.
"""

from pathlib import Path
import argparse
import json
from importlib.metadata import version
import platform
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data_validation import load_inputs


def scores(actual, predicted):
    error = np.asarray(predicted) - np.asarray(actual)
    return {"mae_gwh": float(np.abs(error).mean()),
            "rmse_gwh": float(np.sqrt(np.mean(error ** 2)))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    demand, exported, prices = load_inputs(ROOT)
    daily = demand.to_frame()
    expected_dates = pd.date_range("2023-01-01", "2025-12-31", name="Date")
    if not daily.index.equals(expected_dates):
        raise ValueError("Daily demand must contain every date exactly once in order.")
    if not np.isfinite(daily.energy_gwh).all() or (daily.energy_gwh < 0).any():
        raise ValueError("Demand must be finite and non-negative.")

    features = pd.DataFrame(index=daily.index)
    features["previous_day"] = daily.energy_gwh.shift(1)
    features["previous_week"] = daily.energy_gwh.shift(7)
    features["previous_7_day_mean"] = daily.energy_gwh.shift(1).rolling(7).mean()
    features["weekday"] = pd.Categorical(daily.index.dayofweek, categories=range(7))
    features["month"] = pd.Categorical(daily.index.month, categories=range(1, 13))
    features = pd.get_dummies(features, columns=["weekday", "month"], drop_first=True, dtype=float)
    dataset = features.join(daily).dropna()
    x = dataset.drop(columns="energy_gwh")
    y = dataset.energy_gwh
    train = x.index <= "2024-12-31"
    valid = (x.index > "2024-12-31") & (x.index <= "2025-05-27")
    test = x.index > "2025-05-27"

    # Recreate validation for the selected model, then refit through 27 May.
    validation_model = LinearRegression().fit(x.loc[train], y.loc[train])
    final_model = LinearRegression().fit(x.loc[~test], y.loc[~test])
    prediction = final_model.predict(x.loc[test])
    baseline = scores(y.loc[test], x.loc[test, "previous_week"])
    model = scores(y.loc[test], prediction)
    improvement = 100 * (1 - model["rmse_gwh"] / baseline["rmse_gwh"])

    if not exported.index.equals(x.loc[test].index):
        raise ValueError("App export does not match the notebook's test dates.")
    if not np.isfinite(exported[["Actual", "Forecast", "Last week"]].to_numpy()).all():
        raise ValueError("App export contains non-finite values.")
    np.testing.assert_allclose(exported.Actual, y.loc[test], rtol=0, atol=1e-8)
    np.testing.assert_allclose(exported["Last week"], x.loc[test, "previous_week"], rtol=0, atol=1e-8)

    # The app displays forecasts from its separate model.
    app_metrics = scores(exported.Actual, exported.Forecast)
    if not prices.index.equals(exported.index) or not np.isfinite(prices.price_nzd_mwh).all():
        raise ValueError("Prices must be complete and aligned to the app's dates.")

    report = {
        "test_period": {"first_date": "2025-05-28", "last_date": "2025-12-31", "days": int(test.sum())},
        "split_days": {"training": int(train.sum()), "validation": int(valid.sum()), "test": int(test.sum())},
        "notebook_linear_regression": {
            "validation": scores(y.loc[valid], validation_model.predict(x.loc[valid])),
            "test": model, "test_baseline": baseline,
            "test_rmse_reduction_percent": float(improvement),
        },
        "app_forecast_export": {
            "test": app_metrics,
            "note": "Scored from the committed export; use reproduce_app_forecasts.py to recreate its fit.",
        },
        "environment": {"python": platform.python_version(),
                        **{n: version(n) for n in ["numpy", "pandas", "scikit-learn"]}},
    }
    print(f"Test period: 28 May to 31 December 2025 ({test.sum()} days)")
    print(f"Previous-week baseline RMSE: {baseline['rmse_gwh']:.6f} GWh")
    print(f"Notebook linear regression RMSE: {model['rmse_gwh']:.6f} GWh")
    print(f"Notebook RMSE reduction: {improvement:.1f}%")
    print(f"App forecasting model RMSE: {app_metrics['rmse_gwh']:.6f} GWh")
    print("App dates, actuals, baseline and price coverage checked.")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
