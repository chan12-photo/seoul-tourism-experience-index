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
    "bearer token": re.compile(rb"(?i)Authorization\s*[:=]\s*['\"]?Bearer\s+[A-Za-z0-9._-]{20,}"),
    "GitHub token": re.compile(rb"\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}
BLOCKED_SUFFIXES = {
    ".7z",
    ".dbf",
    ".gpkg",
    ".gz",
    ".numbers",
    ".rar",
    ".shp",
    ".shx",
    ".tar",
    ".xls",
    ".xlsx",
    ".zip",
}
BLOCKED_NAME_PARTS = {"api_key", "apikey", "secret", "credential"}
MAX_PUBLIC_FILE_BYTES = 10 * 1024 * 1024
IGNORED_DIRECTORIES = {".git", ".pytest_cache", ".ruff_cache", ".venv", "__pycache__"}
RESTRICTED_DATA_DIRECTORIES = {
    ("data", "interim"),
    ("data", "processed"),
    ("data", "raw"),
}


def scan_public_tree(root: str | Path) -> list[SafetyFinding]:
    """Find common credential, raw-data, and oversized-file publication risks."""
    base = Path(root).resolve()
    findings: list[SafetyFinding] = []
    for path in base.rglob("*"):
        relative = path.relative_to(base)
        if not path.is_file() or any(part in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        lower_name = path.name.lower()
        if lower_name == ".env" or (
            lower_name.startswith(".env.") and lower_name != ".env.example"
        ):
            findings.append(SafetyFinding(relative, "local environment file must not be committed"))
        if path.name != ".env.example" and any(part in lower_name for part in BLOCKED_NAME_PARTS):
            findings.append(SafetyFinding(relative, "filename suggests a credential"))
        if tuple(relative.parts[:2]) in RESTRICTED_DATA_DIRECTORIES and path.name != ".gitkeep":
            findings.append(SafetyFinding(relative, "research data directory must remain empty"))
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
