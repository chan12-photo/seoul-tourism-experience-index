from collections.abc import Sequence

import numpy as np
import pandas as pd

from .scoring import minmax, shannon_entropy


def add_content_metrics(
    frame: pd.DataFrame,
    *,
    category_columns: Sequence[str],
    total_poi_column: str,
    prefix: str = "C3",
) -> pd.DataFrame:
    """Add content diversity and classification-completion diagnostics."""
    result = frame.copy()
    categories = list(category_columns)
    entropy = shannon_entropy(result, categories)
    counts = result.loc[:, categories].apply(pd.to_numeric, errors="raise")
    result[f"{prefix}_classified_count"] = counts.sum(axis=1)
    result[f"{prefix}_shannon_entropy"] = entropy
    total = pd.to_numeric(result[total_poi_column], errors="coerce")
    if (
        total.isna().any()
        or not np.isfinite(total.to_numpy(dtype=float)).all()
        or (total < 0).any()
    ):
        raise ValueError(f"{total_poi_column} must contain non-negative numeric values")
    classified = pd.to_numeric(result[f"{prefix}_classified_count"], errors="raise")
    if (classified > total).any():
        raise ValueError("Classified category counts cannot exceed total POI counts")
    result["C4_classification_completion_ratio"] = np.divide(
        classified,
        total,
        out=np.zeros(len(result), dtype=float),
        where=total.to_numpy() > 0,
    )
    return result


def add_heritage_metrics(
    frame: pd.DataFrame, *, count_column: str = "C5_heritage_count"
) -> pd.DataFrame:
    """Apply the final log1p transformation used to reduce heritage-count skew."""
    result = frame.copy()
    counts = pd.to_numeric(result[count_column], errors="coerce")
    if (
        counts.isna().any()
        or not np.isfinite(counts.to_numpy(dtype=float)).all()
        or (counts < 0).any()
    ):
        raise ValueError(f"{count_column} must contain non-negative numeric values")
    result["C5_heritage_log_count"] = np.log1p(counts)
    result["C5_heritage_log_score"] = minmax(result["C5_heritage_log_count"])
    return result
