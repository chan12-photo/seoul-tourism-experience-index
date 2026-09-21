from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd


def count_points_by_polygon(
    points: pd.DataFrame,
    boundary_path: str | Path,
    *,
    longitude: str,
    latitude: str,
    boundary_keys: Sequence[str],
    point_id: str | None = None,
    predicate: str = "within",
) -> pd.DataFrame:
    """Count WGS84 point records inside administrative-dong polygons.

    GeoPandas is imported lazily so non-spatial pipeline steps remain lightweight.
    """
    boundary_keys = list(boundary_keys)
    if not boundary_keys:
        raise ValueError("At least one boundary key is required")

    required = {longitude, latitude}
    if point_id:
        required.add(point_id)
    missing = sorted(required - set(points.columns))
    if missing:
        raise ValueError(f"Point data is missing required columns: {missing}")

    clean = points.dropna(subset=[longitude, latitude]).copy()
    clean[longitude] = pd.to_numeric(clean[longitude], errors="coerce")
    clean[latitude] = pd.to_numeric(clean[latitude], errors="coerce")
    coordinates = clean[[longitude, latitude]].to_numpy(dtype=float)
    if np.isnan(coordinates).any() or not np.isfinite(coordinates).all():
        raise ValueError("Point coordinates contain non-numeric or infinite values")
    if not clean[longitude].between(-180.0, 180.0).all():
        raise ValueError("Point longitude is outside the valid WGS84 range")
    if not clean[latitude].between(-90.0, 90.0).all():
        raise ValueError("Point latitude is outside the valid WGS84 range")
    if point_id:
        if clean[point_id].isna().any():
            raise ValueError(f"{point_id} must not contain missing values")
        clean = clean.drop_duplicates(point_id)

    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError('Install spatial dependencies with: pip install -e ".[geo]"') from exc
    point_geometry = gpd.points_from_xy(clean[longitude], clean[latitude], crs="EPSG:4326")
    point_geo = gpd.GeoDataFrame(clean, geometry=point_geometry)

    boundaries = gpd.read_file(boundary_path)
    missing_keys = sorted(set(boundary_keys) - set(boundaries.columns))
    if missing_keys:
        raise ValueError(f"Boundary data is missing key columns: {missing_keys}")
    if boundaries.crs is None:
        raise ValueError("Boundary data has no CRS metadata")
    boundaries = boundaries.to_crs("EPSG:4326")

    joined = gpd.sjoin(
        point_geo,
        boundaries.loc[:, [*boundary_keys, "geometry"]],
        how="inner",
        predicate=predicate,
    )
    counts = joined.groupby(boundary_keys, as_index=False).size()
    counts = counts.rename(columns={"size": "point_count"})
    base = boundaries.loc[:, boundary_keys].drop_duplicates()
    result = base.merge(counts, on=boundary_keys, how="left")
    result["point_count"] = result["point_count"].fillna(0).astype(int)
    return result.sort_values(boundary_keys).reset_index(drop=True)
