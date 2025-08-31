import re

EMAIL_RE = re.compile(r"\b[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b")

INJECTION_PATTERNS = [
    r"ignore\s+all\s+previous\s+instructions",
    r"ignore\s+previous\s+instructions",
    r"forget\s+previous\s+instructions",
    r"system\s*prompt",
    r"jailbreak",
]

BANNED_PATTERNS = [
    r"\bmalware\b",
    r"\bhack\b",
    r"\bexploit\b",
]

def mask_pii(text: str) -> str:
    """Mask common PII like emails and phone numbers in ``text``.

    Returns the masked text.
    """
    if not text:
        return text
    text = EMAIL_RE.sub("[EMAIL]", text)
    text = PHONE_RE.sub("[PHONE]", text)
    return text

def detect_prompt_injection(text: str) -> bool:
    """Return ``True`` if ``text`` contains prompt injection patterns."""
    if not text:
        return False
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False

def filter_output(text: str) -> bool:
    """Return ``True`` if ``text`` contains banned content."""
    if not text:
        return False
    for pattern in BANNED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            return True
    return False
