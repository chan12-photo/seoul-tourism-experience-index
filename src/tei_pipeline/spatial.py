from collections.abc import Sequence
from pathlib import Path

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
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError('Install spatial dependencies with: pip install -e ".[geo]"') from exc

    required = {longitude, latitude}
    if point_id:
        required.add(point_id)
    missing = sorted(required - set(points.columns))
    if missing:
        raise ValueError(f"Point data is missing required columns: {missing}")

    clean = points.dropna(subset=[longitude, latitude]).copy()
    if point_id:
        clean = clean.drop_duplicates(point_id)
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
    counts = joined.groupby(list(boundary_keys), as_index=False).size(name="point_count")
    base = boundaries.loc[:, list(boundary_keys)].drop_duplicates()
    result = base.merge(counts, on=list(boundary_keys), how="left")
    result["point_count"] = result["point_count"].fillna(0).astype(int)
    return result.sort_values(list(boundary_keys)).reset_index(drop=True)

