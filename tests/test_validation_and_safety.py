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
            (root / "api_key.txt").write_text(f"KAKAO_REST_API_KEY={fake_secret}", encoding="utf-8")
            (root / "source.xlsx").write_bytes(b"not a real workbook")
            reasons = [finding.reason for finding in scan_public_tree(root)]
            self.assertTrue(any("credential" in reason for reason in reasons))
            self.assertTrue(any("binary/raw data" in reason for reason in reasons))

    def test_example_env_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".env.example").write_text("KAKAO_REST_API_KEY=\n", encoding="utf-8")
            self.assertEqual(scan_public_tree(root), [])

    def test_restricted_data_archives_and_local_env_are_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = root / "data" / "raw"
            raw.mkdir(parents=True)
            (raw / "source.csv").write_text("id,value\n1,2\n", encoding="utf-8")
            (root / "backup.zip").write_bytes(b"not a real archive")
            (root / ".env.local").write_text("DEBUG=true\n", encoding="utf-8")
            reasons = [finding.reason for finding in scan_public_tree(root)]
            self.assertTrue(any("research data" in reason for reason in reasons))
            self.assertTrue(any("binary/raw data" in reason for reason in reasons))
            self.assertTrue(any("environment file" in reason for reason in reasons))

    def test_blank_admin_key_is_reported(self) -> None:
        frame = pd.DataFrame({"code": ["1", "  "]})
        errors = validate_administrative_dongs(frame, key_columns=["code"], expected_rows=2)
        self.assertTrue(any("blank" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
