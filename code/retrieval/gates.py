from __future__ import annotations

import re
from dataclasses import dataclass, field

from code.loading.corpus import CORPUS

_MASK = "[redacted]"


@dataclass
class PiiReport:
    found: bool = False
    fields: list[str] = field(default_factory=list)
    cleaned: str = ""
    warning: str = ""


@dataclass
class IntentDecision:
    kind: str | None  # "advice" | "returns" | None
    reason: str = ""


_PAN = re.compile(r"\b[A-Za-z]{5}[0-9]{4}[A-Za-z]\b")
_AADHAAR = re.compile(r"\b[2-9][0-9]{11}\b|\b[2-9][0-9]{3}[ \-][0-9]{4}[ \-][0-9]{4}\b")
_PHONE = re.compile(r"\b[6-9][0-9]{9}\b|\b[6-9][0-9]{4}[ \-][0-9]{5}\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[A-Za-z.]+\b")
_OTP = re.compile(
    r"\b(otp|pin|verification code)\b.{0,30}?\b[0-9]{4,8}\b|\b[0-9]{4,8}\b.{0,30}?\b(otp|pin)\b",
    re.IGNORECASE,
)
_ACCOUNT = re.compile(r"\b[0-9]{12,18}\b")

_PII_PATTERNS = (
    ("pan", _PAN),
    ("aadhaar", _AADHAAR),
    ("account number", _ACCOUNT),
    ("phone", _PHONE),
    ("email", _EMAIL),
    ("otp", _OTP),
)


def check_pii(text: str) -> PiiReport:
    """Detect and mask PAN / Aadhaar / account / OTP / email / phone."""
    cleaned = text or ""
    matched: list[str] = []
    for name, pattern in _PII_PATTERNS:
        if pattern.search(cleaned):
            matched.append(name)
            cleaned = pattern.sub(_MASK, cleaned)
    warning = ""
    if matched:
        warning = (
            "Please do not share personal identifiers (PAN, Aadhaar, account, "
            "OTP, email, phone). They were removed and not stored or logged."
        )
    return PiiReport(found=bool(matched), fields=matched, cleaned=cleaned, warning=warning)


_ADVICE_EXPLICIT = re.compile(
    r"\b(should i|am i|worth it|worth investing|is it a good|is this a good"
    r"|is \w[\w .&()-]{0,25}? (a )?good (fund|investment|option)|are \w[\w .&()-]{0,25}? (a )?good"
    r"|best fund|which is better|which performed better|better fund|do you recommend"
    r"|advice|advise|recommend\w*|allocat\w*|rebalanc\w*|build (a |my )?portfolio"
    r"|put (the|my) money|invest the money|buy or sell|good time to|diversif\w*"
    r"|safe to (invest|buy))\b",
    re.IGNORECASE,
)
_ACTION_VERB = re.compile(r"\b(buy|sell|redeem|switch|withdraw|hold) (it |these |units |the fund )?", re.IGNORECASE)
_HOW_TO = re.compile(r"\bhow (to|do|can|should)?\s*\w*\s*(buy|sell|invest|redeem|switch)\b", re.IGNORECASE)

_RETURNS = re.compile(
    r"\b(returns|cagr|annualiz\w*|annual(i|y) return\w*|compound\w* return\w*|"
    r"performed better|outperform\w*|beat (the|a |the index )?|compare\w*|comparison|"
    r"versus|vs\.?|\bvs\b|higher return\w*|more return\w*|growth rate|since inception)\b",
    re.IGNORECASE,
)

_OTHER_AMC = re.compile(
    r"\b(sbi|icici|nippon|axis |tata |parag |parikh|quant |franklin|kotak|baroda|"
    r"aditya birla|edelweiss|mahindra|motilal|utis)\b",
    re.IGNORECASE,
)
_OTHER_HDFC_FUND = re.compile(
    r"hdfc (top 100|mid|value|index|equity savings|infrastructure|"
    r"banking|technology|consumption|focused|arbitrage|defence|pharma)\b",
    re.IGNORECASE,
)


def detect_intent(text: str) -> IntentDecision:
    """Advice / returns intent gate. Returns None for factual questions."""
    body = text or ""
    how_to = _HOW_TO.search(body)
    if _ADVICE_EXPLICIT.search(body):
        return IntentDecision("advice", "advice / recommendation language detected")
    if _ACTION_VERB.search(body) and not how_to:
        return IntentDecision("advice", "buy / sell action detected")
    if _RETURNS.search(body):
        return IntentDecision("returns", "returns / comparison language detected")
    return IntentDecision(None)


def off_corpus_fund(text: str) -> bool:
    """True if the question points at an asset manager or fund outside the five."""
    body = text or ""
    return bool(_OTHER_AMC.search(body) or _OTHER_HDFC_FUND.search(body))


def named_corpus_funds(text: str) -> list[str]:
    """Return the source URLs whose fund keyword appears in the question."""
    body = (text or "").lower()
    hits: list[str] = []
    for entry in CORPUS:
        keywords = _fund_keywords(entry)
        for keyword in keywords:
            if keyword in body:
                hits.append(entry["source_url"])
                break
    return hits


def _fund_keywords(entry: dict[str, str]) -> list[str]:
    theme = entry["theme"]
    name = entry["fund_name"].lower()
    slug = entry["slug"]
    words = {theme, "flexi cap" if theme == "flexi-cap" else theme, "hdfc " + theme}
    if theme == "elss":
        words |= {"elss", "tax saver", "taxsaving", "tax saving"}
    if theme == "flexi-cap":
        words |= {"flexi", "equity fund", "equity-fund"}
    if theme == "large-cap":
        words |= {"large cap", "largecap"}
    if theme == "small-cap":
        words |= {"small cap", "smallcap"}
    if theme == "hybrid":
        words |= {"balanced advantage", "balanced advantage fund"}
    words |= {"hdfc " + slug.replace("hdfc-", "").replace("-fund-direct-growth", "").replace("-", " ").strip()}
    return [w for w in words if w]