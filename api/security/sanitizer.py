"""
Pre-indexing sanitizer for post content.

Detects prompt injection patterns before embedding and before injecting
into agent context. This is the primary defense against PoisonedRAG attacks.

SECURITY: Any changes to this file must be reviewed carefully.
Read api/security/wrappers.py for the runtime injection defense.
"""

import re
import unicodedata

# Patterns that indicate prompt injection attempts
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(previous|all|above|prior)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"new\s+instruction", re.IGNORECASE),
    re.compile(r"act\s+as\s+", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"disregard\s+(your|all|previous)", re.IGNORECASE),
    re.compile(r"<!--.*?(inject|prompt|instruction|override).*?-->", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*script", re.IGNORECASE),
    re.compile(r"<\s*iframe", re.IGNORECASE),
]

# Zero-width and invisible characters used for steganographic injection
_INVISIBLE_CHARS = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\u2060\u2061\u2062\u2063\ufeff]"
)


class SanitizationResult:
    def __init__(self, content: str, flagged: bool, reasons: list[str]) -> None:
        self.content = content
        self.flagged = flagged
        self.reasons = reasons


def sanitize(content: str) -> SanitizationResult:
    """
    Sanitize post content before indexing.

    Returns a SanitizationResult. If flagged=True, the post should be
    quarantined and reviewed before entering the public index.
    """
    reasons: list[str] = []

    # Normalize unicode to detect homoglyph attacks
    normalized = unicodedata.normalize("NFKC", content)

    # Remove invisible characters
    cleaned = _INVISIBLE_CHARS.sub("", normalized)
    if cleaned != normalized:
        reasons.append("invisible_chars_removed")

    # Check for injection patterns
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(cleaned):
            reasons.append(f"injection_pattern:{pattern.pattern[:40]}")

    flagged = len(reasons) > 0
    return SanitizationResult(content=cleaned, flagged=flagged, reasons=reasons)


def is_safe_for_indexing(content: str) -> tuple[bool, list[str]]:
    """Returns (safe, reasons). Posts with safe=False must NOT be indexed."""
    result = sanitize(content)
    # invisible chars alone = warn but index; injection patterns = block
    blocking_reasons = [r for r in result.reasons if r.startswith("injection_pattern")]
    return len(blocking_reasons) == 0, result.reasons
