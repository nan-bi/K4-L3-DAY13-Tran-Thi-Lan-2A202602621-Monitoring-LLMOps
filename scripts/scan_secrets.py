#!/usr/bin/env python3
"""
scripts/scan_secrets.py
Bonus automation: Secret & PII scanner to prevent accidental leakage of sensitive keys, tokens, or raw PII before git commit.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SECRET_PATTERNS = {
    "langfuse_secret_key": re.compile(r"sk-lf-[a-zA-Z0-9_-]{20,}"),
    "generic_api_key": re.compile(r"""(?:api[_-]?key|secret|password|token)\s*[:=]\s*['"][a-zA-Z0-9_\-\.]{16,}['"]""", re.IGNORECASE),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
}

PII_PATTERNS = {
    "raw_email": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!vinuni\.edu\.vn)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "raw_phone_vn": re.compile(r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)"),
    "raw_cccd": re.compile(r"\b\d{12}\b"),
    "raw_credit_card": re.compile(r"\b(?:\d{4}[- ]?){3}\d{4}\b"),
}

IGNORED_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache"}
IGNORED_FILES = {
    "sample_queries.jsonl",   # test dataset
    "test_pii.py",            # unit tests
    "test_validate_logs.py",  # test mock
    "validate_logs.py",       # validator definitions
    "pii.py",                 # regex definitions
    "scan_secrets.py",        # this script
    "05-pii-redaction.txt",   # demonstration of raw vs redacted test cases
}


def scan_file(path: Path) -> list[str]:
    findings = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [f"Cannot read {path}: {e}"]

    # Secret scanning
    for name, pattern in SECRET_PATTERNS.items():
        matches = pattern.findall(content)
        if matches:
            findings.append(f"Secret [{name}] found in {path.name}: {len(matches)} occurrences")

    # PII scanning (only for files in data/ or submission/)
    if "data" in path.parts or "submission" in path.parts:
        if path.name not in IGNORED_FILES:
            for name, pattern in PII_PATTERNS.items():
                matches = pattern.findall(content)
                # Filter out redacted tokens
                filtered = [m for m in matches if "[REDACTED" not in m]
                if filtered:
                    findings.append(f"PII [{name}] found in {path.name}: {len(filtered)} occurrences")

    return findings


def main() -> int:
    print("=== Scanning repository for secrets & unredacted PII ===")
    violations = []
    
    for path in REPO_ROOT.rglob("*"):
        if path.is_file():
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.name in IGNORED_FILES:
                continue
            if path.name == ".env":
                # Ensure .env does not contain actual secrets when committing
                continue
            findings = scan_file(path)
            violations.extend(findings)

    if violations:
        print("[FAILED] Found potential security violations:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print("[PASSED] No leaked secrets or raw PII detected in repo files!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
