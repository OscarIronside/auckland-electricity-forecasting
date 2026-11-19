# Verification

Verified locally on 20 November 2026 using Python 3.14.3 on macOS, with a newly created environment and the supplied dependency versions. This machine already has the OpenMP runtime needed by XGBoost.

| Check | Result |
| --- | --- |
| Fresh installation | App, evaluation and full notebook requirements installed successfully |
| Dependency consistency | `python -m pip check` passed |
| Complete notebook | All 35 code cells executed without notebook errors in the fresh environment |
| Regression checks | All 18 tests passed |
| Forecast-date display | All 218 dates checked, with matching forecast and benchmark values |
| Actual-demand control | Both states checked |
| Purchasing calculation | 12 price/resale combinations matched independent row-by-row calculations |
| Incomplete prices | Removing one price date now stops the app before any metrics are shown |
| Other invalid inputs | Missing files/columns/days, duplicate dates, non-numeric or non-finite values, negative forecasts and mismatched actuals/benchmarks rejected |
| Timestamp regression | Notebook completeness check passed across both daylight-saving transitions with nanosecond and microsecond indexes |
| Notebook model | Test RMSE 0.948777 GWh, MAE 0.658474 GWh |
| Previous-week benchmark | Test RMSE 1.613599 GWh |
| Relative RMSE reduction | 41.2012% |
| App forecasting model | All 218 forecasts recreated and matched the committed export to numerical precision |
| App-model metrics | RMSE 0.789128 GWh, MAE 0.573424 GWh |
| Browser | Both revised views loaded, the actual-demand chart rendered and the purchasing explanation opened |

## Repeat the checks

From the repository root with the app and evaluation dependencies installed:

```bash
python -m pip check
python -m unittest discover -s tests -v
python scripts/reproduce_results.py
python scripts/reproduce_app_forecasts.py
```

With the full notebook dependencies and the system prerequisites from [Setup](SETUP.md):

```bash
python scripts/run_notebook.py
```

The runner saves refreshed output under `reports/`, leaving the committed notebook unchanged. The selected-model report is in [reproduced_metrics.json](reproduced_metrics.json), and input checksums are in [data_manifest.json](data_manifest.json).

## Automated checks

The [GitHub Actions workflow](../.github/workflows/verify.yml) installs the smaller dependency sets and runs the tests and both model reproductions on Ubuntu, macOS and Windows with Python 3.14. A separate Ubuntu job executes the complete notebook.

Workflow configuration alone is not proof of a pass. Check the [actual run results](https://github.com/OscarIronside/auckland-electricity-forecasting/actions) for the commit being reviewed. Until a run has completed successfully, the corresponding platform remains unverified.

No hosted deployment or production forecast service is claimed. The historical information-availability and purchasing assumptions remain as described in [Evaluation](EVALUATION.md).
