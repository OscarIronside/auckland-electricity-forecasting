"""Validate the historical demonstration inputs before displaying results."""

from pathlib import Path
import math

import pandas as pd


class InputDataError(ValueError):
    """An input file cannot support a complete, consistent demonstration."""


def _read_daily_file(root, name, columns):
    try:
        frame = pd.read_csv(Path(root) / name)
    except (OSError, UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise InputDataError(f"Cannot read {name}. Restore the file from the repository.") from exc
    missing = {"Date", *columns} - set(frame.columns)
    if missing:
        raise InputDataError(f"{name} is missing columns: {', '.join(sorted(missing))}.")
    if frame.empty:
        raise InputDataError(f"{name} contains no observations.")
    try:
        dates = pd.DatetimeIndex(pd.to_datetime(frame["Date"], errors="raise"), name="Date")
    except (ValueError, TypeError) as exc:
        raise InputDataError(f"{name} contains invalid dates.") from exc
    if dates.hasnans or dates.tz is not None or not dates.equals(dates.normalize()):
        raise InputDataError(f"{name} must use complete local dates without times or time zones.")
    if not dates.is_unique or not dates.is_monotonic_increasing:
        raise InputDataError(f"{name} must contain each date once, in ascending order.")
    if not dates.equals(pd.date_range(dates[0], dates[-1], name="Date")):
        raise InputDataError(f"{name} has missing days. Restore complete daily coverage.")
    try:
        numeric = frame[columns].apply(pd.to_numeric, errors="raise").astype(float)
    except (ValueError, TypeError) as exc:
        raise InputDataError(f"{name} contains non-numeric values.") from exc
    if not numeric.map(math.isfinite).all().all():
        raise InputDataError(f"{name} contains missing or non-finite values.")
    numeric.index = dates
    return numeric


def load_inputs(root):
    """Return complete demand, forecasts and prices, or a clear input error.

    Prices may be negative. Electricity quantities must be non-negative, and
    the previous-week benchmark must be positive for the percentage display.
    """
    daily = _read_daily_file(root, "daily_demand.csv", ["energy_gwh"])["energy_gwh"]
    results = _read_daily_file(root, "historical_forecasts.csv", ["Actual", "Forecast", "Last week"])
    prices = _read_daily_file(root, "otahuhu_daily_prices.csv", ["price_nzd_mwh"])
    if daily.lt(0).any() or results.lt(0).any().any():
        raise InputDataError("Demand and forecast quantities must be non-negative.")
    if results["Last week"].le(0).any():
        raise InputDataError("Previous-week demand must be positive to compare percentage changes.")
    if not prices.index.equals(results.index):
        raise InputDataError("Prices must cover every forecast date exactly once. Restore otahuhu_daily_prices.csv.")
    actual = daily.reindex(results.index)
    previous_week = daily.reindex(results.index - pd.Timedelta(days=7))
    if actual.isna().any() or previous_week.isna().any():
        raise InputDataError("Daily demand must cover all forecast dates and their previous-week benchmarks.")
    if any(abs(a - b) > 1e-8 for a, b in zip(results.Actual, actual)):
        raise InputDataError("Forecast actuals do not match daily_demand.csv.")
    if any(abs(a - b) > 1e-8 for a, b in zip(results["Last week"], previous_week)):
        raise InputDataError("Previous-week benchmarks do not match daily_demand.csv.")
    return daily, results, prices
