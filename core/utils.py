import locale
import re
import unicodedata
from dateutil import parser as date_parser

__all__ = [
    "safe_slug",
    "normalize_whitespace",
    "parse_dk_amount",
    "parse_dk_date",
    "format_currency",
]

try:
    locale.setlocale(locale.LC_ALL, "da_DK.UTF-8")
except locale.Error:
    pass


def safe_slug(value: str, max_length: int = 120) -> str:
    """Return a filesystem-friendly slug derived from ``value``."""
    if not value:
        return "Uden_navn"
    normalized = unicodedata.normalize("NFKD", value)
    normalized = re.sub(r'[\/\n\r:*?"<>|]', "_", normalized)
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[^A-Za-z0-9._-]", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_.")
    return normalized[:max_length] or "Uden_navn"


def normalize_whitespace(value: str) -> str:
    """Collapse consecutive whitespace and trim leading/trailing spaces."""
    return re.sub(r"\s+", " ", (value or "")).strip()


def parse_dk_amount(value: str) -> str:
    """Parse Danish-formatted amounts to a canonical decimal string."""
    if not value:
        return ""
    cleaned = value.strip().replace(" ", "")
    if re.search(r"\d,\d{1,2}$", cleaned) or ("," in cleaned and "." in cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    return match.group(0) if match else ""


def parse_dk_date(value: str) -> str:
    """Parse a Danish/European date string to ISO format if possible."""
    if not value:
        return ""
    try:
        return date_parser.parse(value, dayfirst=True, fuzzy=True).date().isoformat()
    except Exception:
        return value


def format_currency(value: str) -> str:
    """Format a numeric string as Danish currency (grouped, comma decimals)."""
    if not value:
        return ""
    try:
        amount = float(value)
    except Exception:
        return value
    formatted = locale.format_string("%'.2f", amount, grouping=True)
    return formatted.replace(".", "X").replace(",", ".").replace("X", ",")
