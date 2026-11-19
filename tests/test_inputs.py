"""Regression checks for incomplete or inconsistent historical inputs."""

from pathlib import Path
import sys
import tempfile
import unittest

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data_validation import InputDataError, load_inputs


class InputValidationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        dates = pd.date_range("2025-01-01", periods=22)
        demand = pd.Series(range(100, 122), index=dates, dtype=float)
        pd.DataFrame({"Date": dates, "energy_gwh": demand.to_numpy()}).to_csv(self.root / "daily_demand.csv", index=False)
        targets = dates[14:]
        pd.DataFrame({"Date": targets, "Actual": demand.loc[targets].to_numpy(),
                      "Forecast": demand.loc[targets].to_numpy() + 0.5,
                      "Last week": demand.loc[targets - pd.Timedelta(days=7)].to_numpy()}).to_csv(self.root / "historical_forecasts.csv", index=False)
        pd.DataFrame({"Date": targets, "price_nzd_mwh": 200.0}).to_csv(self.root / "otahuhu_daily_prices.csv", index=False)

    def change(self, filename, change):
        path = self.root / filename
        frame = pd.read_csv(path)
        change(frame).to_csv(path, index=False)

    def test_valid_inputs_and_negative_market_price(self):
        self.change("otahuhu_daily_prices.csv", lambda f: f.assign(price_nzd_mwh=-10.0))
        daily, forecasts, prices = load_inputs(self.root)
        self.assertEqual((len(daily), len(forecasts), len(prices)), (22, 8, 8))

    def test_missing_price_day_is_rejected(self):
        self.change("otahuhu_daily_prices.csv", lambda f: f.iloc[1:])
        with self.assertRaisesRegex(InputDataError, "cover every forecast date"):
            load_inputs(self.root)

    def test_non_finite_prices_are_rejected(self):
        for value in [float("nan"), float("inf"), -float("inf")]:
            with self.subTest(value=value):
                self.change("otahuhu_daily_prices.csv", lambda f: f.assign(price_nzd_mwh=value))
                with self.assertRaisesRegex(InputDataError, "non-finite"):
                    load_inputs(self.root)

    def test_invalid_price_text_is_rejected(self):
        self.change("otahuhu_daily_prices.csv", lambda f: f.assign(price_nzd_mwh="unknown"))
        with self.assertRaisesRegex(InputDataError, "non-numeric"):
            load_inputs(self.root)

    def test_duplicate_dates_are_rejected(self):
        self.change("historical_forecasts.csv", lambda f: pd.concat([f.iloc[:1], f], ignore_index=True))
        with self.assertRaisesRegex(InputDataError, "each date once"):
            load_inputs(self.root)

    def test_missing_forecast_day_is_rejected(self):
        self.change("historical_forecasts.csv", lambda f: f.drop(index=3))
        with self.assertRaisesRegex(InputDataError, "missing days"):
            load_inputs(self.root)

    def test_missing_required_column_is_rejected(self):
        self.change("historical_forecasts.csv", lambda f: f.drop(columns="Forecast"))
        with self.assertRaisesRegex(InputDataError, "missing columns: Forecast"):
            load_inputs(self.root)

    def test_invalid_dates_are_rejected(self):
        self.change("historical_forecasts.csv", lambda f: f.assign(Date="not-a-date"))
        with self.assertRaisesRegex(InputDataError, "invalid dates"):
            load_inputs(self.root)

    def test_actuals_must_match_demand(self):
        self.change("historical_forecasts.csv", lambda f: f.assign(Actual=f.Actual + 1))
        with self.assertRaisesRegex(InputDataError, "actuals do not match"):
            load_inputs(self.root)

    def test_benchmark_must_match_demand(self):
        self.change("historical_forecasts.csv", lambda f: f.assign(**{"Last week": f["Last week"] + 1}))
        with self.assertRaisesRegex(InputDataError, "benchmarks do not match"):
            load_inputs(self.root)

    def test_zero_benchmark_is_rejected_before_percentage_calculation(self):
        self.change("historical_forecasts.csv", lambda f: f.assign(**{"Last week": 0}))
        with self.assertRaisesRegex(InputDataError, "must be positive"):
            load_inputs(self.root)

    def test_negative_forecast_is_rejected(self):
        self.change("historical_forecasts.csv", lambda f: f.assign(Forecast=-1))
        with self.assertRaisesRegex(InputDataError, "non-negative"):
            load_inputs(self.root)

    def test_missing_file_has_actionable_error(self):
        (self.root / "otahuhu_daily_prices.csv").unlink()
        with self.assertRaisesRegex(InputDataError, "Cannot read otahuhu_daily_prices.csv"):
            load_inputs(self.root)

    def test_published_data_passes(self):
        daily, results, prices = load_inputs(ROOT)
        self.assertEqual((len(daily), len(results), len(prices)), (1096, 218, 218))


if __name__ == "__main__":
    unittest.main()
