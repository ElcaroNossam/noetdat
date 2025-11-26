"""
Template filters for formatting numeric values, especially prices and volumes.
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def format_price(value):
    """
    Adaptive price formatting:
    - price >= 1: 2 decimal places (e.g., 51234.56)
    - 0.01 <= price < 1: 4 decimal places
    - price < 0.01: 8 decimal places
    """
    if value is None:
        return ""

    try:
        if isinstance(value, Decimal):
            v = float(value)
        else:
            v = float(value)
    except (ValueError, TypeError):
        return str(value)

    abs_v = abs(v)

    if abs_v >= 1:
        return f"{v:.2f}"
    elif abs_v >= 0.01:
        return f"{v:.4f}"
    else:
        return f"{v:.8f}"


@register.filter
def format_volume(value):
    """
    Format volume with K/M/B suffixes:
    - >= 1B: show as X.XXB
    - >= 1M: show as X.XXM
    - >= 1K: show as X.XXK
    - < 1K: show as is with 2 decimals
    """
    if value is None:
        return ""

    try:
        if isinstance(value, Decimal):
            v = float(value)
        else:
            v = float(value)
    except (ValueError, TypeError):
        return str(value)

    abs_v = abs(v)

    if abs_v >= 1_000_000_000:
        return f"{v / 1_000_000_000:.2f}B"
    elif abs_v >= 1_000_000:
        return f"{v / 1_000_000:.2f}M"
    elif abs_v >= 1_000:
        return f"{v / 1_000:.2f}K"
    else:
        return f"{v:.2f}"

