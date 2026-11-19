# Included data and provenance

The included files contain public regional electricity and weather data used in the coursework. They contain no customer inspection records or individual household data.

| File | Rows | Purpose |
| --- | ---: | --- |
| `data/forecast_dataset.csv` | 52,608 | Half-hourly regional demand for full notebook and app-model reproduction |
| `data/weather_hourly.csv` | 26,304 | Hourly ERA5 reanalysis for the app model |
| `daily_demand.csv` | 1,096 | Daily demand in GWh for the app and selected notebook-model reproduction |
| `historical_forecasts.csv` | 218 | App forecasts, actual demand and previous-week benchmark |
| `otahuhu_daily_prices.csv` | 218 | Daily price proxy for the purchasing simulation |

## Electricity

Source: [Electricity Authority EMI reconciled injection and offtake](https://www.emi.ea.govt.nz/Wholesale/Datasets/Volumes/Reconciliation).

The coursework selected offtake for Vector's Waitemata and Auckland reporting regions, IDs 3 and 4, and summed kWh by trading interval. This is a regional selection and does not exactly match Auckland's administrative boundaries. The included series covers 1 January 2023 to 31 December 2025 in Pacific/Auckland time. UTC distinguishes repeated local times during daylight-saving transitions.

The half-hourly file is the coursework's aggregated input, not the full underlying EMI record-level extraction. Daily demand is the sum of those intervals divided by 1,000,000 to convert kWh to GWh. The original demand files were retrieved for the coursework on 3 October 2026 and include later revisions. The limitation around historical publication timing is described in [Evaluation](EVALUATION.md).

## Weather

Source: [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api), ERA5 reanalysis.

The coursework requested temperature, relative humidity, precipitation and wind speed at latitude -36.8485, longitude 174.7633, with UTC timestamps. Wind speed is in metres per second. The series covers the same complete Auckland local days as electricity; it was retrieved on 3 October 2026. This is a representative location, rather than weather at every point in the demand region.

The app's forecasting model uses weather from the preceding day. Reanalysis is a retrospective product and does not establish what would have been known at a real forecast cutoff.

## Prices

Source: [Electricity Authority EMI final energy prices](https://www.emi.ea.govt.nz/Wholesale/Datasets/DispatchAndPricing/FinalEnergyPrices/ByMonth), node OTA2201 at Otahuhu. The source record is retained in [price_sources.json](price_sources.json).

Prices are unweighted arithmetic means of final half-hourly prices for each local trading day, in NZD per MWh. They are a simulation proxy, not a customer tariff. The 31 December 2025 value came from the daily file because the original monthly source was incomplete.

Retain these source attributions when sharing the included datasets. Data-provider terms apply separately from project code.
