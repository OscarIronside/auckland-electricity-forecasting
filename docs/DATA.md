# Data sources

All inputs are included in the repository.

| File | Rows | Contents |
| --- | ---: | --- |
| `data/forecast_dataset.csv` | 52,608 | Half-hourly regional electricity demand |
| `data/weather_hourly.csv` | 26,304 | Hourly weather for the app model |
| `daily_demand.csv` | 1,096 | Daily demand in GWh |
| `historical_forecasts.csv` | 218 | App forecasts, actual demand and previous-week benchmark |
| `otahuhu_daily_prices.csv` | 218 | Daily prices and interval counts |

## Electricity demand

Source: [Electricity Authority EMI reconciled injection and offtake](https://www.emi.ea.govt.nz/Wholesale/Datasets/Volumes/Reconciliation), retrieved on 3 October 2026.

The coursework combined offtake for Vector's Waitemata and Auckland reporting regions, IDs 3 and 4. This represents regional demand and does not exactly follow Auckland's administrative boundaries. The half-hourly file contains the aggregated coursework input.

The series covers 1 January 2023 to 31 December 2025 in Auckland local time. UTC timestamps distinguish the repeated times when daylight saving ends. Daily totals are the sum of kWh divided by 1,000,000 to give GWh, with 46, 48 or 50 intervals depending on the length of the local day.

These records include later revisions. The [evaluation notes](EVALUATION.md) explain how that limits the historical results.

## Weather

Source: [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api), using ERA5 reanalysis, retrieved on 3 October 2026.

The hourly series contains temperature, relative humidity, precipitation and wind speed at latitude -36.8485, longitude 174.7633. Timestamps use UTC, and wind speed is in metres per second. It covers the same Auckland local days as demand. The location is one representative point in the region.

The app model uses weather from the preceding day. ERA5 is a retrospective dataset, so this does not establish when those observations would have been available for a live forecast.

## Prices

Source: [Electricity Authority EMI final energy prices](https://www.emi.ea.govt.nz/Wholesale/Datasets/DispatchAndPricing/FinalEnergyPrices/ByMonth), node OTA2201 at Otahuhu, retrieved on 9 October 2026.

The series covers 28 May to 31 December 2025. Prices are arithmetic averages of the final half-hourly prices for each local day, in NZD/MWh. There are 46 intervals on 28 September and 48 on the other included days. The average gives each interval equal weight.

Monthly files from May to December supplied the prices. The [December file](https://www.emi.ea.govt.nz/Wholesale/Datasets/DispatchAndPricing/FinalEnergyPrices/ByMonth/202512_FinalEnergyPrices_incomplete.csv) was incomplete, so 31 December came from the [daily file](https://www.emi.ea.govt.nz/Wholesale/Datasets/DispatchAndPricing/FinalEnergyPrices/20251231_FinalEnergyPrices.csv).

The daily average is used as a regional price estimate in the simulation. It is not a customer tariff. Retain the source attributions when sharing the data; the providers' terms apply separately from the project code.
