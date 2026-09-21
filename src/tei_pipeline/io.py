from pathlib import Path

import pandas as pd


def read_csv(path: str | Path, **kwargs: object) -> pd.DataFrame:
    """Read a CSV while handling the two encodings used in the source project."""
    source = Path(path)
    errors: list[UnicodeDecodeError] = []
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(source, encoding=encoding, **kwargs)
        except UnicodeDecodeError as exc:
            errors.append(exc)
    raise errors[-1]


def write_csv(frame: pd.DataFrame, path: str | Path) -> None:
    """Write a CSV with an Excel-friendly UTF-8 byte-order mark."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(target, index=False, encoding="utf-8-sig")
