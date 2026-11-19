# Evaluation

## Models and test period

The notebook compares linear regression, random forest and XGBoost. Its inputs are demand from one and seven days earlier, the preceding seven-day mean, weekday and month. The rolling mean excludes the day being predicted.

The split follows time order:

| Period | Dates | Days after creating lag features |
| --- | --- | ---: |
| Training | 8 January 2023 to 31 December 2024 | 724 |
| Validation | 1 January to 27 May 2025 | 147 |
| Test | 28 May to 31 December 2025 | 218 |

The stronger tree model is tuned using time-series folds within the training period. Models are then compared on validation RMSE. The selected linear regression is refitted using training and validation data before the final test. The test period is kept out of model selection and tuning.

Its test RMSE is 0.948777 GWh, against 1.613599 GWh for the previous-week benchmark. The 41.2% reduction is calculated as `(benchmark RMSE - model RMSE) / benchmark RMSE`.

The app uses a separate linear regression with additional weather and calendar features. It has RMSE of 0.789128 GWh and MAE of 0.573424 GWh on the same dates. `scripts/reproduce_app_forecasts.py` recreates that fit and checks all predictions against `historical_forecasts.csv`.

## What the results show

Each test forecast uses the observed history before that date. These are individual daily predictions, not a forecast of all 218 days made at the start of the period.

Demand records include later revisions, and weather comes from retrospective reanalysis. We have not reconstructed when each input was available. A live forecasting assessment would need to account for publication delays and revisions.

Performance also varies by season. For example, notebook-model RMSE is about 1.445 GWh in June and 0.321 GWh in November. This variation does not mean the fixed model learned or improved during testing.

SHAP plots explain how features contribute to a fitted model's predictions. They do not show cause and effect, and correlated demand lags make individual contributions harder to interpret.

## Input checks

The full notebook checks half-hourly timestamps for duplicates, gaps and missing values before daily aggregation. It also checks interval counts across daylight-saving changes. The selected-model script starts with the daily CSV, while the app-model script uses the included half-hourly demand and hourly weather.

The app checks that demand, forecasts, benchmarks and prices are complete and consistent before displaying results.

## Purchasing simulation

The simulation buys the forecast amount at the selected advance price. If demand is higher, it buys the shortfall at the daily Otahuhu price. If demand is lower, it resells the surplus at the selected percentage of that price. Both forecasts use the same rules, with GWh converted to MWh before calculating costs.

The daily price is an unweighted average. The simulation omits interval-level exposure, network charges, retailer margins, transaction costs and customer tariffs. It also assumes the forecast quantity can be bought and any surplus resold as specified. The displayed saving depends on those assumptions, and a more accurate forecast can still cost more in some scenarios.

The next useful evaluation would use the information available at each actual decision time, test more seasons and compare costs under realistic purchasing rules.
