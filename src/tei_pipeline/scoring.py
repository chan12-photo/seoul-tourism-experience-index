from collections.abc import Sequence

import numpy as np
import pandas as pd


def _numeric(series: pd.Series, name: str) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").astype(float)
    if values.isna().any():
        bad_rows = values.index[values.isna()].tolist()[:5]
        raise ValueError(f"{name} contains missing or non-numeric values at rows {bad_rows}")
    if not np.isfinite(values.to_numpy()).all():
        raise ValueError(f"{name} contains infinite values")
    return values


def minmax(series: pd.Series, *, constant_value: float = 0.0) -> pd.Series:
    """Scale a numeric series to [0, 1] without silently accepting missing data."""
    values = _numeric(series, series.name or "series")
    minimum = float(values.min())
    maximum = float(values.max())
    if np.isclose(maximum, minimum):
        return pd.Series(constant_value, index=values.index, name=series.name, dtype=float)
    return (values - minimum) / (maximum - minimum)


def reverse_minmax(series: pd.Series) -> pd.Series:
    """Scale a cost or distance variable so that a smaller value receives a higher score."""
    return 1.0 - minmax(series)


def zscore(series: pd.Series) -> pd.Series:
    """Return a population-standardized series."""
    values = _numeric(series, series.name or "series")
    std = float(values.std(ddof=0))
    if np.isclose(std, 0.0):
        return pd.Series(0.0, index=values.index, name=series.name, dtype=float)
    return (values - float(values.mean())) / std


def shannon_entropy(frame: pd.DataFrame, columns: Sequence[str]) -> pd.Series:
    """Calculate row-wise Shannon entropy from non-negative category counts."""
    counts = frame.loc[:, list(columns)].apply(pd.to_numeric, errors="coerce")
    if counts.isna().any().any():
        raise ValueError("Category counts contain missing or non-numeric values")
    if (counts < 0).any().any():
        raise ValueError("Category counts must be non-negative")

    values = counts.to_numpy(dtype=float)
    totals = values.sum(axis=1, keepdims=True)
    proportions = np.divide(values, totals, out=np.zeros_like(values), where=totals > 0)
    logs = np.zeros_like(proportions)
    np.log(proportions, out=logs, where=proportions > 0)
    entropy = -(proportions * logs).sum(axis=1)
    return pd.Series(entropy, index=frame.index, name="shannon_entropy")

