"""Daily data preparation and features for the app's forecasting model."""

import numpy as np
import pandas as pd

WEATHER_COLUMNS = [
    "mean_temperature", "min_temperature", "max_temperature", "mean_humidity",
    "precipitation", "mean_wind", "max_wind",
]

NATIONAL_HOLIDAY_DATES = {
    2023: ["01-01", "01-02", "02-06", "04-07", "04-10", "04-25", "06-05", "07-14", "10-23", "12-25", "12-26"],
    2024: ["01-01", "01-02", "02-06", "03-29", "04-01", "04-25", "06-03", "06-28", "10-28", "12-25", "12-26"],
    2025: ["01-01", "01-02", "02-06", "04-18", "04-21", "04-25", "06-02", "06-20", "10-27", "12-25", "12-26"],
}

AUCKLAND_ANNIVERSARY_DATES = ["2023-01-30", "2024-01-29", "2025-01-27"]

SCHOOL_HOLIDAY_RANGES = [
    ("2023-01-01", "2023-01-29"), ("2023-04-07", "2023-04-23"),
    ("2023-07-01", "2023-07-16"), ("2023-09-23", "2023-10-08"), ("2023-12-21", "2023-12-31"),
    ("2024-01-01", "2024-01-28"), ("2024-04-02", "2024-04-02"),
    ("2024-04-13", "2024-04-28"), ("2024-07-06", "2024-07-21"),
    ("2024-09-28", "2024-10-13"), ("2024-12-21", "2024-12-31"),
    ("2025-01-01", "2025-01-26"), ("2025-04-12", "2025-04-27"),
    ("2025-06-28", "2025-07-13"), ("2025-09-20", "2025-10-05"), ("2025-12-20", "2025-12-31"),
]


def prepare_daily_data(electricity, weather):
    """Aggregate complete observations into actual Auckland local daily totals."""
    electricity, weather = electricity.copy(), weather.copy()
    for frame, frequency in [(electricity, "30min"), (weather, "1h")]:
        frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
        frame.sort_values("timestamp_utc", inplace=True)
        if (frame.isna().any().any() or not frame.timestamp_utc.is_unique
                or not np.isfinite(frame.select_dtypes(include="number").to_numpy()).all()):
            raise ValueError("Missing or non-finite values, or duplicate timestamps in shared data.")
        if not frame.timestamp_utc.diff().dropna().eq(pd.Timedelta(frequency)).all():
            raise ValueError("Time gaps in shared data.")
    if not electricity.electricity_kwh.ge(0).all():
        raise ValueError("Electricity use must be nonnegative.")
    electricity["date"] = electricity.timestamp_utc.dt.tz_convert("Pacific/Auckland").dt.tz_localize(None).dt.normalize()
    weather["date"] = weather.timestamp_utc.dt.tz_convert("Pacific/Auckland").dt.tz_localize(None).dt.normalize()
    daily = electricity.groupby("date").agg(demand_kwh=("electricity_kwh", "sum"), intervals=("electricity_kwh", "size"))
    daily_weather = weather.groupby("date").agg(
        mean_temperature=("temperature_2m", "mean"), min_temperature=("temperature_2m", "min"),
        max_temperature=("temperature_2m", "max"), mean_humidity=("relative_humidity_2m", "mean"),
        precipitation=("precipitation", "sum"), mean_wind=("wind_speed_10m", "mean"),
        max_wind=("wind_speed_10m", "max"),
    )
    if not daily.index.equals(daily_weather.index):
        raise ValueError("Electricity and weather local date coverage differ.")
    starts = daily.index.tz_localize("Pacific/Auckland").tz_convert("UTC")
    ends = (daily.index + pd.Timedelta(days=1)).tz_localize("Pacific/Auckland").tz_convert("UTC")
    daily["day_hours"] = (ends - starts) / pd.Timedelta(hours=1)
    if not (daily.intervals == daily.day_hours * 2).all():
        raise ValueError("Incomplete electricity days.")
    if not weather.groupby("date").size().eq(daily.day_hours).all():
        raise ValueError("Incomplete weather days.")
    daily = daily.join(daily_weather)
    return daily


def create_forecast_features(daily):
    """Create known calendar and D-1-or-earlier predictors; retain warm-up NaNs."""
    if daily.index.min() < pd.Timestamp("2023-01-01") or daily.index.max() > pd.Timestamp("2025-12-31"):
        raise ValueError("The fixed holiday calendar covers 2023–2025 only.")
    features = pd.DataFrame(index=daily.index)
    features["day_of_week"] = daily.index.dayofweek
    features["is_weekend"] = (daily.index.dayofweek >= 5).astype(int)
    features["month"] = daily.index.month
    features["expected_day_hours"] = daily.day_hours
    for lag in [1, 7, 14]:
        features[f"demand_lag_{lag}"] = daily.demand_kwh.shift(lag)
    features["demand_mean_7"] = daily.demand_kwh.shift(1).rolling(7).mean()
    features["demand_std_7"] = daily.demand_kwh.shift(1).rolling(7).std()

    for column in WEATHER_COLUMNS:
        name = column + "_lag_1"
        features[name] = daily[column].shift(1)
    features["heating_need_lag_1"] = (18 - daily.mean_temperature.shift(1)).clip(lower=0)
    features["cooling_need_lag_1"] = (daily.mean_temperature.shift(1) - 18).clip(lower=0)
    features["temperature_range_lag_1"] = (daily.max_temperature - daily.min_temperature).shift(1)

    national_dates = pd.to_datetime([f"{year}-{date}" for year, dates in NATIONAL_HOLIDAY_DATES.items() for date in dates] + ["2023-01-03"])
    holiday_dates = national_dates.union(pd.to_datetime(AUCKLAND_ANNIVERSARY_DATES))
    boundary_dates = holiday_dates.union(pd.DatetimeIndex(["2026-01-01"]))
    features["is_public_holiday"] = features.index.isin(holiday_dates).astype(int)
    features["is_auckland_anniversary"] = features.index.isin(pd.to_datetime(AUCKLAND_ANNIVERSARY_DATES)).astype(int)
    features["before_public_holiday"] = (features.index + pd.Timedelta(days=1)).isin(boundary_dates).astype(int)
    features["after_public_holiday"] = (features.index - pd.Timedelta(days=1)).isin(boundary_dates).astype(int)
    features["is_school_holiday"] = 0
    for start, end in SCHOOL_HOLIDAY_RANGES:
        features.loc[start:end, "is_school_holiday"] = 1
    return features
