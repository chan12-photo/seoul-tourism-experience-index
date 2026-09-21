import unittest

import numpy as np
import pandas as pd

from tei_pipeline.culture import add_content_metrics, add_heritage_metrics


class CultureTests(unittest.TestCase):
    def test_content_metrics_and_completion_ratio(self) -> None:
        frame = pd.DataFrame(
            {
                "traditional": [2, 0],
                "art": [2, 0],
                "nature": [0, 0],
                "modern": [0, 0],
                "total": [5, 0],
            }
        )
        result = add_content_metrics(
            frame,
            category_columns=["traditional", "art", "nature", "modern"],
            total_poi_column="total",
        )
        self.assertAlmostEqual(result.loc[0, "C3_shannon_entropy"], np.log(2.0))
        self.assertAlmostEqual(result.loc[0, "C4_classification_completion_ratio"], 0.8)
        self.assertEqual(result.loc[1, "C4_classification_completion_ratio"], 0.0)

    def test_heritage_log_transform(self) -> None:
        frame = pd.DataFrame({"C5_heritage_count": [0, 1, 9]})
        result = add_heritage_metrics(frame)
        np.testing.assert_allclose(result["C5_heritage_log_count"], np.log1p([0, 1, 9]))
        self.assertEqual(result["C5_heritage_log_score"].iloc[0], 0.0)
        self.assertEqual(result["C5_heritage_log_score"].iloc[-1], 1.0)

    def test_classified_count_cannot_exceed_total(self) -> None:
        frame = pd.DataFrame({"a": [2], "b": [2], "total": [3]})
        with self.assertRaisesRegex(ValueError, "exceed"):
            add_content_metrics(frame, category_columns=["a", "b"], total_poi_column="total")


if __name__ == "__main__":
    unittest.main()

