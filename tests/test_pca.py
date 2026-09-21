import unittest

import numpy as np
import pandas as pd

from tei_pipeline.pca import combine_axis_scores, fit_first_component


class PCATests(unittest.TestCase):
    def test_first_component_for_correlated_features(self) -> None:
        frame = pd.DataFrame({"x": [1, 2, 3, 4], "y": [2, 4, 6, 8]})
        result = fit_first_component(frame, ["x", "y"])
        self.assertAlmostEqual(result.explained_variance_ratio, 1.0)
        self.assertGreater(result.loadings.sum(), 0)
        self.assertAlmostEqual(float(result.scores.mean()), 0.0)
        self.assertAlmostEqual(float(result.scores.std(ddof=0)), 1.0)

    def test_constant_features_are_rejected(self) -> None:
        frame = pd.DataFrame({"x": [1, 1, 1], "y": [1, 2, 3]})
        with self.assertRaisesRegex(ValueError, "constant"):
            fit_first_component(frame, ["x", "y"])

    def test_equal_weight_combination_standardizes_axis_variance(self) -> None:
        frame = pd.DataFrame({"A": [0, 1, 2], "B": [0, 100, 200]})
        standardized = combine_axis_scores(frame, ["A", "B"], standardize_axes=True)
        raw = combine_axis_scores(frame, ["A", "B"], standardize_axes=False)
        np.testing.assert_allclose(standardized, [-1.22474487, 0.0, 1.22474487])
        np.testing.assert_allclose(raw, [0.0, 50.5, 101.0])


if __name__ == "__main__":
    unittest.main()

