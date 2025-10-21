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
    "format_date_long",
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
    except (ValueError, TypeError):
        return value

    # Try to use locale formatting if Danish locale is available
    try:
        formatted = locale.format_string("%.2f", amount, grouping=True)
        # If locale is da_DK, it should already have correct format (123.456,78)
        # If not, we'll swap separators in the fallback
        if "," in formatted or formatted.count(".") > 1:
            # Locale formatting worked, return as is
            return formatted
    except (ValueError, TypeError, locale.Error):
        pass

    # Fallback: format manually for Danish (period as thousands, comma as decimal)
    # First format with standard grouping
    formatted = f"{amount:,.2f}"
    # Swap: comma->period (thousands), period->comma (decimal)
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted


def format_date_long(value: str) -> str:
    """Return a Danish long-form date like ``15. august 2022`` when possible."""
    if not value:
        return ""
    try:
        dt = date_parser.parse(value, dayfirst=True, fuzzy=True)
    except Exception:
        return value

    # Danish month names
    danish_months = {
        1: "januar", 2: "februar", 3: "marts", 4: "april",
        5: "maj", 6: "juni", 7: "juli", 8: "august",
        9: "september", 10: "oktober", 11: "november", 12: "december"
    }

    month_name = danish_months.get(dt.month, dt.strftime("%B").lower())
    return f"{dt.day}. {month_name} {dt.year}"
