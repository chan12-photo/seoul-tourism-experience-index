from collections.abc import Sequence

import numpy as np
import pandas as pd


def validate_administrative_dongs(
    frame: pd.DataFrame,
    *,
    key_columns: Sequence[str],
    expected_rows: int = 426,
) -> list[str]:
    """Return human-readable validation errors for an administrative-dong table."""
    errors: list[str] = []
    if not key_columns:
        return ["at least one key column is required"]
    missing = sorted(set(key_columns) - set(frame.columns))
    if missing:
        return [f"missing key columns: {missing}"]
    if len(frame) != expected_rows:
        errors.append(f"expected {expected_rows} rows, found {len(frame)}")
    if frame.loc[:, list(key_columns)].isna().any().any():
        errors.append("key columns contain missing values")
    blank_columns = [
        column for column in key_columns if frame[column].astype("string").str.strip().eq("").any()
    ]
    if blank_columns:
        errors.append(f"key columns contain blank values: {blank_columns}")
    duplicate_count = int(frame.duplicated(list(key_columns)).sum())
    if duplicate_count:
        errors.append(f"found {duplicate_count} duplicate key rows")
    return errors


def validate_numeric_columns(
    frame: pd.DataFrame,
    columns: Sequence[str],
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> list[str]:
    errors: list[str] = []
    for column in columns:
        if column not in frame.columns:
            errors.append(f"missing numeric column: {column}")
            continue
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.isna().any():
            errors.append(f"{column} contains missing or non-numeric values")
            continue
        if not np.isfinite(values.to_numpy()).all():
            errors.append(f"{column} contains infinite values")
        if minimum is not None and (values < minimum).any():
            errors.append(f"{column} contains values below {minimum}")
        if maximum is not None and (values > maximum).any():
            errors.append(f"{column} contains values above {maximum}")
    return errors
