from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from .scoring import zscore


@dataclass(frozen=True)
class PCAResult:
    scores: pd.Series
    loadings: pd.Series
    explained_variance_ratio: float


def fit_first_component(
    frame: pd.DataFrame,
    features: list[str],
    *,
    score_scale: Literal["none", "zscore"] = "zscore",
    orient_positive: bool = True,
    name: str = "PC1",
) -> PCAResult:
    """Fit PC1 after feature standardization using a deterministic SVD implementation.

    ``score_scale='none'`` reproduces the original combination approach. The recommended
    ``'zscore'`` mode gives each axis comparable variance before equal weighting.
    """
    if len(features) < 2:
        raise ValueError("PCA requires at least two features")
    missing = sorted(set(features) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing PCA features: {missing}")

    numeric = frame.loc[:, features].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any():
        bad = numeric.columns[numeric.isna().any()].tolist()
        raise ValueError(f"PCA features contain missing or non-numeric values: {bad}")
    if len(numeric) < 2:
        raise ValueError("PCA requires at least two rows")

    means = numeric.mean(axis=0)
    standard_deviations = numeric.std(axis=0, ddof=0)
    constant = standard_deviations.index[np.isclose(standard_deviations, 0.0)].tolist()
    if constant:
        raise ValueError(f"PCA features are constant: {constant}")

    standardized = (numeric - means) / standard_deviations
    _, singular_values, components = np.linalg.svd(standardized.to_numpy(), full_matrices=False)
    component = components[0].copy()
    scores = standardized.to_numpy() @ component

    if orient_positive and component.sum() < 0:
        component *= -1.0
        scores *= -1.0

    explained = singular_values**2
    ratio = float(explained[0] / explained.sum())
    score_series = pd.Series(scores, index=frame.index, name=name)
    if score_scale == "zscore":
        score_series = zscore(score_series)
    elif score_scale != "none":
        raise ValueError("score_scale must be 'none' or 'zscore'")

    return PCAResult(
        scores=score_series,
        loadings=pd.Series(component, index=features, name=f"{name}_loading"),
        explained_variance_ratio=ratio,
    )


def combine_axis_scores(
    frame: pd.DataFrame,
    axis_columns: list[str],
    *,
    standardize_axes: bool = True,
    output_column: str = "TEI_supply_score",
) -> pd.Series:
    """Combine axis scores with equal arithmetic weights."""
    if not axis_columns:
        raise ValueError("At least one axis score is required")
    missing = sorted(set(axis_columns) - set(frame.columns))
    if missing:
        raise ValueError(f"Missing axis scores: {missing}")
    scores = frame.loc[:, axis_columns].apply(pd.to_numeric, errors="coerce")
    if scores.isna().any().any():
        raise ValueError("Axis scores contain missing or non-numeric values")
    if standardize_axes:
        scores = scores.apply(zscore, axis=0)
    return scores.mean(axis=1).rename(output_column)

