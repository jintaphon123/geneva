from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SecretFinding:
    pattern_name: str
    line_number: int
    masked_value: str


def _mask(value: str) -> str:
    return value[:4] + "***" if len(value) > 4 else "***"


def detect_secret_patterns(content: str) -> list[SecretFinding]:
    patterns = {
        "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
        "github_token": re.compile(r"(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,255})"),
        "generic_api_key": re.compile(r"(?i)(?:key|token|secret)\s*=\s*([A-Za-z0-9_-]{32,64})"),
        "private_key": re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH) PRIVATE KEY-----"),
    }
    findings: list[SecretFinding] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for pattern_name, pattern in patterns.items():
            for match in pattern.finditer(line):
                value = match.group(1) if match.lastindex else match.group(0)
                findings.append(
                    SecretFinding(
                        pattern_name=pattern_name,
                        line_number=line_number,
                        masked_value=_mask(value),
                    )
                )
    return findings
