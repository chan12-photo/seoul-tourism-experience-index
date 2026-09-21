import unittest

import numpy as np
import pandas as pd

from tei_pipeline.transport import build_transport_features, haversine_km, nearest_hub_distance


class TransportTests(unittest.TestCase):
    def test_haversine_one_degree_at_equator(self) -> None:
        distance = haversine_km([0.0], [0.0], [1.0], [0.0])
        self.assertAlmostEqual(distance[0], 111.195, places=3)

    def test_nearest_hub_selection(self) -> None:
        origins = pd.DataFrame(
            {
                "key": ["west", "east"],
                "longitude": [0.1, 9.9],
                "latitude": [0.0, 0.0],
                "district": ["A", "B"],
            }
        )
        hubs = pd.DataFrame(
            {
                "hub_name": ["left", "right"],
                "longitude": [0.0, 10.0],
                "latitude": [0.0, 0.0],
            }
        )
        result = nearest_hub_distance(origins, hubs, passthrough=["district"])
        self.assertEqual(result["D2_nearest_hub"].tolist(), ["right", "left"])
        self.assertTrue((result["D2_access"] <= 0).all())

    def test_final_transport_names_are_consistent(self) -> None:
        keys = {
            "administrative_dong_code": ["1", "2"],
            "district": ["A", "A"],
            "administrative_dong": ["one", "two"],
            "key": ["A_one", "A_two"],
        }
        subway = pd.DataFrame({**keys, "D1_subway_count": [1, 2]})
        distance = pd.DataFrame({**keys, "D2_min_distance_km": [2.5, 4.0]})
        bus = pd.DataFrame({**keys, "D3_bus_stop_count": [10, 20]})
        result = build_transport_features(subway, distance, bus)
        np.testing.assert_allclose(result["D2_access"], [-2.5, -4.0])
        self.assertIn("D3_bus_stop_count", result.columns)

    def test_invalid_coordinates_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "latitude"):
            haversine_km([127.0], [91.0], [127.1], [37.5])
        with self.assertRaisesRegex(ValueError, "infinite"):
            haversine_km([np.inf], [37.5], [127.1], [37.5])

    def test_transport_tables_must_have_matching_keys(self) -> None:
        subway = pd.DataFrame(
            {
                "administrative_dong_code": ["1"],
                "district": ["A"],
                "administrative_dong": ["one"],
                "key": ["A_one"],
                "D1_subway_count": [1],
            }
        )
        distance = subway.drop(columns="D1_subway_count").assign(D2_min_distance_km=2.5)
        bus = subway.drop(columns="D1_subway_count").assign(
            administrative_dong_code="2", D3_bus_stop_count=10
        )
        with self.assertRaisesRegex(ValueError, "do not match"):
            build_transport_features(subway, distance, bus)


if __name__ == "__main__":
    unittest.main()
