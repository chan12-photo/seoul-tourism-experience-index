import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SafetyFinding:
    path: Path
    reason: str


SECRET_PATTERNS = {
    "credential assignment": re.compile(
        rb"(?i)(?:KAKAO_REST_API_KEY|TMAP_API_KEY|API_KEY)\s*=\s*['\"]?[A-Za-z0-9_-]{20,}"
    ),
    "Kakao authorization header": re.compile(rb"(?i)KakaoAK\s+[A-Za-z0-9_-]{20,}"),
}
BLOCKED_SUFFIXES = {".shp", ".shx", ".dbf", ".gpkg", ".xlsx", ".xls", ".numbers"}
BLOCKED_NAME_PARTS = {"api_key", "apikey", "secret", "credential"}
MAX_PUBLIC_FILE_BYTES = 10 * 1024 * 1024
IGNORED_DIRECTORIES = {".git", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__"}


def scan_public_tree(root: str | Path) -> list[SafetyFinding]:
    """Find common credential, raw-data, and oversized-file publication risks."""
    base = Path(root).resolve()
    findings: list[SafetyFinding] = []
    for path in base.rglob("*"):
        relative = path.relative_to(base)
        if not path.is_file() or any(part in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        lower_name = path.name.lower()
        if lower_name == ".env":
            findings.append(SafetyFinding(relative, "local environment file must not be committed"))
        if path.name != ".env.example" and any(part in lower_name for part in BLOCKED_NAME_PARTS):
            findings.append(SafetyFinding(relative, "filename suggests a credential"))
        if path.suffix.lower() in BLOCKED_SUFFIXES:
            findings.append(SafetyFinding(relative, f"binary/raw data file: {path.suffix.lower()}"))
        if path.stat().st_size > MAX_PUBLIC_FILE_BYTES:
            findings.append(SafetyFinding(relative, "file is larger than 10 MiB"))
        if path.stat().st_size <= MAX_PUBLIC_FILE_BYTES:
            content = path.read_bytes()
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(content):
                    findings.append(SafetyFinding(relative, label))
    return findings
