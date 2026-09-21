import unittest

import numpy as np
import pandas as pd

from tei_pipeline.scoring import minmax, reverse_minmax, shannon_entropy, zscore


class ScoringTests(unittest.TestCase):
    def test_minmax_and_reverse_minmax(self) -> None:
        values = pd.Series([10, 20, 30], name="value")
        np.testing.assert_allclose(minmax(values), [0.0, 0.5, 1.0])
        np.testing.assert_allclose(reverse_minmax(values), [1.0, 0.5, 0.0])

    def test_constant_series_has_stable_scores(self) -> None:
        values = pd.Series([4, 4, 4])
        np.testing.assert_allclose(minmax(values), [0.0, 0.0, 0.0])
        np.testing.assert_allclose(reverse_minmax(values), [1.0, 1.0, 1.0])
        np.testing.assert_allclose(zscore(values), [0.0, 0.0, 0.0])

    def test_shannon_entropy(self) -> None:
        frame = pd.DataFrame({"a": [1, 0], "b": [1, 0], "c": [0, 0]})
        result = shannon_entropy(frame, ["a", "b", "c"])
        self.assertAlmostEqual(result.iloc[0], np.log(2.0))
        self.assertEqual(result.iloc[1], 0.0)

    def test_missing_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing"):
            minmax(pd.Series([1.0, np.nan]))

    def test_entropy_rejects_empty_or_infinite_categories(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one"):
            shannon_entropy(pd.DataFrame({"a": [1]}), [])
        with self.assertRaisesRegex(ValueError, "infinite"):
            shannon_entropy(pd.DataFrame({"a": [np.inf], "b": [1]}), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
