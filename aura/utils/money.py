"""Money formatting helpers for AURA."""

_CURRENCY_SYMBOLS = {
    'INR': '\u20b9',  # ₹
    'USD': '$',
}


def format_amount(amount, currency='INR'):
    """Return formatted amount string with currency symbol (for HTML rendering)."""
    symbol = _CURRENCY_SYMBOLS.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def format_amount_pdf(amount, currency='INR'):
    """Return formatted amount string using ASCII-safe currency codes (for PDF rendering).

    Uses currency codes (e.g. INR, USD) instead of symbols to avoid missing-glyph
    black boxes in PDFs rendered with standard ReportLab/Helvetica fonts.
    """
    code = currency if currency else 'INR'
    return f"{code} {amount:,.2f}"
