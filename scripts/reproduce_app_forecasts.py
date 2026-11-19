"""Recreate the app's linear-regression forecasts from included source data.

This recreates the selected model's fit, not the wider team's model-selection
experiments. The feature code is retained in app_forecasting.py.
"""

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression

from app_forecasting import prepare_daily_data, create_forecast_features, WEATHER_COLUMNS


def main():
    root = Path(__file__).resolve().parents[1]
    daily = prepare_daily_data(pd.read_csv(root / 'data/forecast_dataset.csv'),
                               pd.read_csv(root / 'data/weather_hourly.csv'))
    columns = ['day_of_week', 'is_weekend', 'month', 'expected_day_hours',
               'demand_lag_1', 'demand_lag_7', 'demand_lag_14',
               'demand_mean_7', 'demand_std_7']
    columns += [c + '_lag_1' for c in WEATHER_COLUMNS]
    columns += ['is_public_holiday', 'is_auckland_anniversary', 'before_public_holiday',
                'after_public_holiday', 'is_school_holiday']
    dataset = create_forecast_features(daily).join(daily.demand_kwh).dropna()
    development = dataset.loc[:'2025-05-27']
    test = dataset.loc['2025-05-28':'2025-12-31']
    calendar = ['day_of_week', 'month']
    numeric = [c for c in columns if c not in calendar]
    encode = ColumnTransformer([
        ('calendar', OneHotEncoder(categories=[list(range(7)), list(range(1, 13))],
                                  drop='first', handle_unknown='ignore', sparse_output=False), calendar),
        ('numeric', 'passthrough', numeric),
    ])
    model = Pipeline([('encode', encode), ('scale', StandardScaler()), ('model', LinearRegression())])
    model.fit(development[columns], development.demand_kwh)
    predicted = model.predict(test[columns]) / 1_000_000
    exported = pd.read_csv(root/'historical_forecasts.csv', parse_dates=['Date']).set_index('Date')
    if not test.index.equals(exported.index):
        raise ValueError('Recreated and exported test dates differ.')
    np.testing.assert_allclose(predicted, exported.Forecast, atol=1e-8, rtol=0)
    actual = test.demand_kwh.to_numpy() / 1_000_000
    np.testing.assert_allclose(actual, exported.Actual, atol=1e-8, rtol=0)
    error = predicted - actual
    print(f'App forecasts recreated for {len(predicted)} test dates.')
    print(f'MAE: {np.abs(error).mean():.6f} GWh')
    print(f'RMSE: {np.sqrt(np.mean(error**2)):.6f} GWh')
    print(f'Maximum difference from committed forecasts: {np.max(np.abs(predicted-exported.Forecast)):.12f} GWh')


if __name__ == '__main__':
    main()
