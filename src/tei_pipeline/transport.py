from collections.abc import Sequence

import numpy as np
import pandas as pd

from .scoring import reverse_minmax

EARTH_RADIUS_KM = 6371.0


def haversine_km(
    origin_lon: pd.Series | np.ndarray,
    origin_lat: pd.Series | np.ndarray,
    destination_lon: pd.Series | np.ndarray,
    destination_lat: pd.Series | np.ndarray,
) -> np.ndarray:
    """Return great-circle distances in kilometres for WGS84-like coordinates."""
    lon1 = np.radians(np.asarray(origin_lon, dtype=float))
    lat1 = np.radians(np.asarray(origin_lat, dtype=float))
    lon2 = np.radians(np.asarray(destination_lon, dtype=float))
    lat2 = np.radians(np.asarray(destination_lat, dtype=float))

    coordinate_sets = {
        "origin longitude": (lon1, np.pi),
        "destination longitude": (lon2, np.pi),
        "origin latitude": (lat1, np.pi / 2.0),
        "destination latitude": (lat2, np.pi / 2.0),
    }
    for label, (values, limit) in coordinate_sets.items():
        if not np.isfinite(values).all():
            raise ValueError(f"{label} contains missing or infinite values")
        if (np.abs(values) > limit).any():
            raise ValueError(f"{label} is outside the valid WGS84 range")

    delta_lon = lon2 - lon1
    delta_lat = lat2 - lat1
    a = np.sin(delta_lat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2.0) ** 2
    a = np.clip(a, 0.0, 1.0)
    return EARTH_RADIUS_KM * 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))


def nearest_hub_distance(
    origins: pd.DataFrame,
    hubs: pd.DataFrame,
    *,
    origin_id: str = "key",
    origin_lon: str = "longitude",
    origin_lat: str = "latitude",
    hub_name: str = "hub_name",
    hub_lon: str = "longitude",
    hub_lat: str = "latitude",
    passthrough: Sequence[str] = (),
) -> pd.DataFrame:
    """Find each origin's nearest hub using a transparent straight-line proxy."""
    origin_columns = [origin_id, origin_lon, origin_lat, *passthrough]
    hub_columns = [hub_name, hub_lon, hub_lat]
    if len(origin_columns) != len(set(origin_columns)):
        raise ValueError("Origin and passthrough column names must be unique")
    if len(hub_columns) != len(set(hub_columns)):
        raise ValueError("Hub column names must be unique")
    _require_columns(origins, origin_columns, "origins")
    _require_columns(hubs, hub_columns, "hubs")
    if origins[origin_id].isna().any():
        raise ValueError(f"origins.{origin_id} must not contain missing values")
    if origins[origin_id].duplicated().any():
        raise ValueError(f"origins.{origin_id} must be unique")
    if hubs[hub_name].isna().any() or hubs[hub_name].duplicated().any():
        raise ValueError(f"hubs.{hub_name} must contain unique, non-missing values")
    if origins.empty or hubs.empty:
        raise ValueError("origins and hubs must both contain at least one row")

    left = origins.loc[:, origin_columns].rename(
        columns={origin_lon: "origin_lon", origin_lat: "origin_lat"}
    )
    right = hubs.loc[:, hub_columns].rename(columns={hub_lon: "hub_lon", hub_lat: "hub_lat"})
    pairs = left.merge(right, how="cross")
    pairs["D2_min_distance_km"] = haversine_km(
        pairs["origin_lon"], pairs["origin_lat"], pairs["hub_lon"], pairs["hub_lat"]
    )
    nearest_index = pairs.groupby(origin_id)["D2_min_distance_km"].idxmin()
    result = pairs.loc[nearest_index].copy()
    result = result.rename(columns={hub_name: "D2_nearest_hub"})
    result["D2_distance_score"] = reverse_minmax(result["D2_min_distance_km"])
    result["D2_access"] = -result["D2_min_distance_km"]
    output_columns = [
        origin_id,
        *passthrough,
        "D2_nearest_hub",
        "D2_min_distance_km",
        "D2_distance_score",
        "D2_access",
    ]
    return result.loc[:, output_columns].sort_values(origin_id).reset_index(drop=True)


def build_transport_features(
    subway: pd.DataFrame,
    distance: pd.DataFrame,
    bus: pd.DataFrame,
    *,
    keys: Sequence[str] = ("administrative_dong_code", "district", "administrative_dong", "key"),
) -> pd.DataFrame:
    """Merge the final report's D1, D2, and D3 raw PCA features."""
    key_columns = list(keys)
    if not key_columns:
        raise ValueError("At least one administrative-dong key is required")
    if len(key_columns) != len(set(key_columns)):
        raise ValueError("Administrative-dong key columns must be unique")
    _require_columns(subway, [*key_columns, "D1_subway_count"], "subway")
    _require_columns(distance, [*key_columns, "D2_min_distance_km"], "distance")
    _require_columns(bus, [*key_columns, "D3_bus_stop_count"], "bus")
    for name, frame in (("subway", subway), ("distance", distance), ("bus", bus)):
        if frame.loc[:, key_columns].isna().any().any():
            raise ValueError(f"{name} contains missing administrative-dong keys")
        if frame.duplicated(key_columns).any():
            raise ValueError(f"{name} contains duplicate administrative-dong keys")

    reference_keys = pd.MultiIndex.from_frame(subway.loc[:, key_columns])
    for name, frame in (("distance", distance), ("bus", bus)):
        candidate_keys = pd.MultiIndex.from_frame(frame.loc[:, key_columns])
        missing_keys = reference_keys.difference(candidate_keys)
        extra_keys = candidate_keys.difference(reference_keys)
        if len(missing_keys) or len(extra_keys):
            raise ValueError(
                f"{name} administrative-dong keys do not match subway "
                f"(missing={len(missing_keys)}, extra={len(extra_keys)})"
            )

    _require_non_negative_numeric(subway["D1_subway_count"], "D1_subway_count")
    _require_non_negative_numeric(distance["D2_min_distance_km"], "D2_min_distance_km")
    _require_non_negative_numeric(bus["D3_bus_stop_count"], "D3_bus_stop_count")

    merged = subway[key_columns + ["D1_subway_count"]].merge(
        distance[key_columns + ["D2_min_distance_km"]], on=key_columns, validate="one_to_one"
    )
    merged = merged.merge(
        bus[key_columns + ["D3_bus_stop_count"]], on=key_columns, validate="one_to_one"
    )
    merged["D2_access"] = -pd.to_numeric(merged["D2_min_distance_km"], errors="raise")
    return merged[
        key_columns + ["D1_subway_count", "D2_min_distance_km", "D2_access", "D3_bus_stop_count"]
    ]


def _require_columns(frame: pd.DataFrame, columns: Sequence[str], label: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def _require_non_negative_numeric(series: pd.Series, label: str) -> None:
    values = pd.to_numeric(series, errors="coerce")
    if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError(f"{label} must contain finite numeric values")
    if (values < 0).any():
        raise ValueError(f"{label} must contain non-negative values")
