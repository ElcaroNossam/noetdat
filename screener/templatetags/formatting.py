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


@register.filter
def format_vdelta(value):
    """
    Format volume delta with K/M/B suffixes and smart rounding:
    - >= 1M: show as X.XXM
    - >= 1K: show as X.XXK
    - >= 1: show as integer or 1 decimal
    - < 1: show with 2 decimals
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

    if abs_v >= 1_000_000:
        return f"{v / 1_000_000:.2f}M"
    elif abs_v >= 1_000:
        return f"{v / 1_000:.2f}K"
    elif abs_v >= 1:
        # For values >= 1, show as integer if whole number, otherwise 1 decimal
        if abs_v == int(abs_v):
            return f"{int(v)}"
        else:
            return f"{v:.1f}"
    else:
        return f"{v:.2f}"


@register.filter
def format_percentage(value, decimals=2):
    """
    Format percentage with specified decimal places.
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

    return f"{v:.{decimals}f}"


@register.filter
def format_volatility(value):
    """
    Format volatility with smart rounding:
    - >= 1: 2 decimals
    - < 1: 3 decimals
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
    else:
        return f"{v:.3f}"


@register.filter
def format_oi_change(value):
    """
    Format OI change percentage with smart rounding:
    - >= 1: 2 decimals
    - >= 0.1: 3 decimals
    - < 0.1: 4 decimals
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
    elif abs_v >= 0.1:
        return f"{v:.3f}"
    else:
        return f"{v:.4f}"

