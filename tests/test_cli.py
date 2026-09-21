import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd


class CLIIntegrationTests(unittest.TestCase):
    def test_pca_command_writes_scores_and_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "features.csv"
            output = root / "scores.csv"
            pd.DataFrame(
                {
                    "administrative_dong_code": ["001", "002", "003"],
                    "x": [1, 2, 3],
                    "y": [2, 4, 6],
                }
            ).to_csv(source, index=False)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tei_pipeline",
                    "pca-axis",
                    "--input",
                    str(source),
                    "--features",
                    "x",
                    "y",
                    "--output-column",
                    "axis_pc1",
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("explained_variance_ratio=1.000000", completed.stdout)
            result = pd.read_csv(
                output, encoding="utf-8-sig", dtype={"administrative_dong_code": "string"}
            )
            self.assertEqual(
                result.columns.tolist(), ["administrative_dong_code", "x", "y", "axis_pc1"]
            )
            self.assertEqual(result["administrative_dong_code"].tolist(), ["001", "002", "003"])
            self.assertAlmostEqual(float(result["axis_pc1"].mean()), 0.0)

    def test_validate_command_returns_nonzero_for_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.csv"
            pd.DataFrame({"code": ["1", "1"]}).to_csv(source, index=False)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tei_pipeline",
                    "validate-admin",
                    "--input",
                    str(source),
                    "--keys",
                    "code",
                    "--expected-rows",
                    "2",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("duplicate key rows", completed.stdout)

    def test_data_error_is_reported_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "constant.csv"
            output = root / "scores.csv"
            pd.DataFrame({"x": [1, 1], "y": [2, 3]}).to_csv(source, index=False)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tei_pipeline",
                    "pca-axis",
                    "--input",
                    str(source),
                    "--features",
                    "x",
                    "y",
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("ERROR: PCA features are constant", completed.stderr)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
