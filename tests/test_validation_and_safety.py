import tempfile
import unittest
from pathlib import Path

import pandas as pd

from tei_pipeline.safety import scan_public_tree
from tei_pipeline.validation import validate_administrative_dongs


class ValidationAndSafetyTests(unittest.TestCase):
    def test_duplicate_admin_key_is_reported(self) -> None:
        frame = pd.DataFrame({"code": ["1", "1"]})
        errors = validate_administrative_dongs(frame, key_columns=["code"], expected_rows=2)
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_secret_and_binary_data_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_secret = "abcdefghijklm" + "nopqrstuvwxyz123456"
            (root / "api_key.txt").write_text(
                f"KAKAO_REST_API_KEY={fake_secret}", encoding="utf-8"
            )
            (root / "source.xlsx").write_bytes(b"not a real workbook")
            reasons = [finding.reason for finding in scan_public_tree(root)]
            self.assertTrue(any("credential" in reason for reason in reasons))
            self.assertTrue(any("binary/raw data" in reason for reason in reasons))

    def test_example_env_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env.example").write_text("KAKAO_REST_API_KEY=\n", encoding="utf-8")
            self.assertEqual(scan_public_tree(root), [])


if __name__ == "__main__":
    unittest.main()
