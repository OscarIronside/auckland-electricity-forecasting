# Verification

Checked on 20 November 2026 using Python 3.14.3 on macOS, in a fresh environment. The machine already had the OpenMP runtime required by XGBoost.

| Check | Result |
| --- | --- |
| Installation | App, model and full notebook dependencies installed; `pip check` passed |
| Regression tests | All 18 passed |
| App dates | All 218 dates displayed the expected forecast and benchmark |
| Actual-demand toggle | Both states checked |
| Purchasing calculations | 12 price/resale combinations matched independent calculations |
| Invalid data | Missing files, columns or dates, duplicate dates, invalid values and mismatched actuals or benchmarks were rejected |
| Missing prices | App stopped before displaying metrics |
| Daylight saving | Both transitions checked with nanosecond and microsecond timestamps |
| Notebook result | RMSE 0.948777 GWh against benchmark 1.613599 GWh; reduction 41.2% |
| App model | All 218 forecasts recreated; RMSE 0.789128 GWh |
| Full notebook | All 35 code cells executed without errors |
| Browser | Both app views and their controls checked |

## Run the checks

After installing the app and model dependencies from the [README](../README.md):

```bash
python -m pip check
python -m unittest discover -s tests -v
python scripts/reproduce_results.py
python scripts/reproduce_app_forecasts.py
```

To run all notebook cells, install the full requirements and follow the [notebook prerequisites](../README.md#run-the-full-notebook), then run:

```bash
python scripts/run_notebook.py
```

The runner saves an executed copy under `reports/`. The reproduction scripts print their results. To save a JSON report as well:

```bash
python scripts/reproduce_results.py --output reports/metrics.json
```

## GitHub checks

The [workflow](../.github/workflows/verify.yml) runs app tests and both model reproductions on Ubuntu, macOS and Windows. A separate Ubuntu job runs the full notebook. The [run history](https://github.com/OscarIronside/auckland-electricity-forecasting/actions) shows the outcome for each commit.

These checks cover the historical project. They do not test a hosted app or live forecasting service.
