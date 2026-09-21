import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from tei_pipeline.spatial import count_points_by_polygon


class SpatialValidationTests(unittest.TestCase):
    def test_points_are_counted_and_duplicate_ids_removed(self) -> None:
        boundaries = gpd.GeoDataFrame(
            {"code": ["left", "right"]},
            geometry=[box(0.0, 0.0, 1.0, 1.0), box(1.0, 0.0, 2.0, 1.0)],
            crs="EPSG:4326",
        )
        points = pd.DataFrame(
            {
                "point_id": ["a", "a", "b", "missing-coordinate"],
                "longitude": [0.5, 0.5, 1.5, None],
                "latitude": [0.5, 0.5, 0.5, None],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            boundary_path = Path(directory) / "boundaries.geojson"
            boundaries.to_file(boundary_path, driver="GeoJSON")
            result = count_points_by_polygon(
                points,
                boundary_path,
                longitude="longitude",
                latitude="latitude",
                boundary_keys=["code"],
                point_id="point_id",
            )

        self.assertEqual(result["code"].tolist(), ["left", "right"])
        self.assertEqual(result["point_count"].tolist(), [1, 1])

    def test_invalid_point_coordinates_fail_before_spatial_io(self) -> None:
        points = pd.DataFrame({"longitude": [181.0], "latitude": [37.5]})
        with self.assertRaisesRegex(ValueError, "longitude"):
            count_points_by_polygon(
                points,
                "unused.geojson",
                longitude="longitude",
                latitude="latitude",
                boundary_keys=["code"],
            )

    def test_boundary_key_is_required(self) -> None:
        points = pd.DataFrame({"longitude": [127.0], "latitude": [37.5]})
        with self.assertRaisesRegex(ValueError, "boundary key"):
            count_points_by_polygon(
                points,
                "unused.geojson",
                longitude="longitude",
                latitude="latitude",
                boundary_keys=[],
            )


if __name__ == "__main__":
    unittest.main()
