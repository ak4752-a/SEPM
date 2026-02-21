"""Money formatting helpers for AURA."""

_CURRENCY_SYMBOLS = {
    'INR': '\u20b9',  # ₹
    'USD': '$',
}


def format_amount(amount, currency='INR'):
    """Return formatted amount string with currency symbol."""
    symbol = _CURRENCY_SYMBOLS.get(currency, currency)
    return f"{symbol}{amount:,.2f}"
