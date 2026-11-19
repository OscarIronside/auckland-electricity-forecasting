"""Check the complete historical date range, costs and data-error display."""

from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class AppTests(unittest.TestCase):
    def test_all_dates_and_actual_demand(self):
        forecasts = pd.read_csv(ROOT / "historical_forecasts.csv", parse_dates=["Date"]).set_index("Date")
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.tabs), 2)
        for date, row in forecasts.iterrows():
            with self.subTest(date=str(date.date())):
                app.date_input[0].set_value(date.date()).run()
                self.assertFalse(app.exception)
                self.assertEqual(app.metric[0].value, f"{row.Forecast:.2f} GWh")
                self.assertEqual(app.metric[1].value, f"{row['Last week']:.2f} GWh")
        app.checkbox[0].check().run()
        self.assertTrue(any("actual electricity use" in m.value for m in app.markdown))
        app.checkbox[0].uncheck().run()
        self.assertFalse(any("actual electricity use" in m.value for m in app.markdown))

    def test_purchasing_costs_against_independent_calculation(self):
        forecasts = pd.read_csv(ROOT / "historical_forecasts.csv", parse_dates=["Date"]).set_index("Date")
        prices = pd.read_csv(ROOT / "otahuhu_daily_prices.csv", parse_dates=["Date"]).set_index("Date")
        app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20).run()
        for contract in [0.0, 100.0, 200.0, 1000.0]:
            for resale in [0, 50, 100]:
                with self.subTest(contract=contract, resale=resale):
                    app.number_input[0].set_value(contract)
                    app.slider[0].set_value(resale).run()
                    self.assertFalse(app.exception)
                    costs = {}
                    for name, column in [("baseline", "Last week"), ("model", "Forecast")]:
                        total = 0.0
                        for date, row in forecasts.iterrows():
                            required, purchased = row.Actual * 1000, row[column] * 1000
                            market = prices.loc[date, "price_nzd_mwh"]
                            total += purchased * contract
                            if required > purchased:
                                total += (required - purchased) * market
                            else:
                                total -= (purchased - required) * market * resale / 100
                        costs[name] = total
                    saving = costs["baseline"] - costs["model"]
                    self.assertEqual(app.metric[3].value, f"NZ${costs['baseline'] / 1_000_000:.2f}m")
                    self.assertEqual(app.metric[4].value, f"NZ${costs['model'] / 1_000_000:.2f}m")
                    self.assertEqual(app.metric[5].value, f"NZ${abs(saving):,.0f}")
                    self.assertEqual(app.metric[5].label, "Simulated saving" if saving >= 0 else "Extra cost vs benchmark")

    def test_missing_price_stops_app_before_any_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ["app.py", "data_validation.py", "daily_demand.csv", "historical_forecasts.csv", "otahuhu_daily_prices.csv"]:
                shutil.copy2(ROOT / name, root / name)
            prices = pd.read_csv(root / "otahuhu_daily_prices.csv")
            prices.iloc[1:].to_csv(root / "otahuhu_daily_prices.csv", index=False)
            app = AppTest.from_file(str(root / "app.py"), default_timeout=20).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.error), 1)
            self.assertIn("cover every forecast date", app.error[0].value)
            self.assertEqual(len(app.metric), 0)


class DatetimeRegressionTests(unittest.TestCase):
    def test_notebook_completeness_check_in_both_timestamp_units(self):
        notebook = json.loads((ROOT / "forecasting.ipynb").read_text())
        source = next("".join(c["source"]) for c in notebook["cells"]
                      if c["cell_type"] == "code" and "next_midnights =" in "".join(c["source"]))
        import numpy as np
        for start, expected in [("2025-04-05", [48, 50, 48]), ("2025-09-27", [48, 46, 48])]:
            for unit in ["ns", "us"]:
                with self.subTest(start=start, unit=unit):
                    boundaries = pd.date_range(start, periods=4, tz="Pacific/Auckland").as_unit(unit)
                    index = pd.date_range(boundaries[0], boundaries[-1], freq="30min", inclusive="left").as_unit(unit)
                    local = pd.Series(1.0, index=index)
                    scope = {"np": np, "pd": pd, "local": local, "daily": local.resample("D").sum()}
                    exec(compile(source, "notebook-completeness-cell", "exec"), scope)
                    self.assertEqual(list(scope["expected"]), expected)


if __name__ == "__main__":
    unittest.main()
