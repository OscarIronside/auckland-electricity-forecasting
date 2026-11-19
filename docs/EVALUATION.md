# Evaluation and limitations

## What the headline result means

The notebook linear regression has test RMSE of 0.948777 GWh, compared with 1.613599 GWh for a seasonal-naive forecast using demand from seven days earlier. The reduction is calculated as `(baseline RMSE - model RMSE) / baseline RMSE`, or approximately 41.2%. It describes one historical test period, not accuracy on future production data.

The separate `historical_forecasts.csv` contains predictions from the app's forecasting model. Its RMSE is 0.789128 GWh and MAE is 0.573424 GWh for the same dates. `scripts/reproduce_app_forecasts.py` recreates that selected linear-regression fit using the included half-hourly demand and hourly weather inputs, then checks the predictions against the export. It does not rerun the wider group's model-selection experiments.

## Forecast protocol

The notebook creates demand lags of one and seven days and a seven-day rolling mean shifted by one day. Weekday and month are encoded as categorical features. Using shifted data avoids directly including the target day's demand in its inputs.

The split is chronological: train through 31 December 2024, select using validation through 27 May 2025, then evaluate on 28 May to 31 December 2025. The selected linear regression is refitted through the validation end date before test prediction. The notebook also compares two tree models and tunes the better tree family using time-series folds within the training period.

Each test prediction uses the observed demand history preceding that date. This corresponds to a sequence of one-step predictions under an assumed availability of recent observations. It is not a recursive 218-day forecast from a single starting point. Reconciled electricity data may be published or revised later, so an operational backtest must reconstruct what was actually known at each forecast time.

## Data preparation

The original half-hourly dataset contains 52,608 intervals. The notebook checks for unique UTC timestamps, missing values, non-negative demand and continuous half-hourly spacing. It converts to Pacific/Auckland before daily aggregation and checks expected interval counts on daylight-saving transition days. The resulting daily series contains 1,096 dates.

The selected-model script uses the already aggregated daily CSV. It checks contiguous dates and finite, non-negative demand, but does not independently repeat the raw extraction or half-hourly checks. The full notebook runner uses the included half-hourly dataset and repeats the notebook's checks. The app reproduction script also validates the half-hourly and weather inputs through the shared feature code.

## Reading the results

MAE gives the average absolute error in daily energy. RMSE gives more weight to large errors. Both are expressed in GWh and should be compared on the same dates. Lower forecast error is useful evidence, but the right model for an actual purchasing decision would also need evaluation against that decision's financial consequences.

Performance varies across the test period. The notebook linear regression's June RMSE is about 1.445 GWh, compared with 0.321 GWh in November. These monthly results describe different seasonal conditions and sample sizes; they do not establish that the model is improving over time.

SHAP values in the notebook describe how features contribute to that fitted model's predictions relative to its chosen background data. They are not causal effects. Correlated lag features also limit how individual feature attributions should be interpreted.

## Purchasing simulation

The app converts GWh to MWh and buys the forecast amount at the chosen fixed contract price. Shortfalls are purchased at the daily price proxy; surplus is resold at the selected fraction of that price. The benchmark uses the same rules with last week's demand.

Otahuhu's unweighted daily final-price average does not capture demand-weighted interval exposure, network charges, retailer margins, hedging constraints, transaction costs or an individual customer tariff. The simulation assumes the forecast quantity can be bought at the chosen contract price and surplus can be resold under the selected rule. A displayed saving is an outcome of those assumptions, not a measured commercial result.

## What to improve first

1. Define the intended user, forecast horizon and actual decision being supported.
2. Reconstruct data publication and revision timing, then evaluate with realistic availability.
3. Use rolling evaluation across more seasons, with interval estimates and diagnostic checks.
4. Evaluate cost under a validated purchasing model, alongside MAE and RMSE.
5. Package a versioned inference interface with input checks, operational monitoring and a clear owner.

## Verification

Run `python scripts/reproduce_results.py` from the repository root. The pinned evaluation dependencies record the environment used for the repository's verification. `docs/reproduced_metrics.json` records the numerical result and package versions. The app can be run independently using `requirements-demo.txt`.
