"""
Utility functions for formatting values (same logic as template filters).
"""
from decimal import Decimal


def format_volume(value):
    """
    Format volume with K/M/B suffixes:
    - >= 1B: show as X.XXB
    - >= 1M: show as X.XXM
    - >= 1K: show as X.XXK
    - < 1K: show as is with 2 decimals
    """
    if value is None:
        return "0.00"

    try:
        if isinstance(value, Decimal):
            v = float(value)
        else:
            v = float(value)
    except (ValueError, TypeError):
        return "0.00"

    if v == 0:
        return "0.00"
    
    abs_v = abs(v)

    if abs_v >= 1_000_000_000:
        return f"{v / 1_000_000_000:.2f}B"
    elif abs_v >= 1_000_000:
        return f"{v / 1_000_000:.2f}M"
    elif abs_v >= 1_000:
        return f"{v / 1_000:.2f}K"
    else:
        return f"{v:.2f}"


def format_vdelta(value):
    """
    Format volume delta with K/M/B suffixes and smart rounding:
    - >= 1M: show as X.XXM
    - >= 1K: show as X.XXK
    - >= 1: show as integer or 1 decimal
    - < 1: show with 2 decimals
    """
    if value is None:
        return "0.00"

    try:
        if isinstance(value, Decimal):
            v = float(value)
        else:
            v = float(value)
    except (ValueError, TypeError):
        return "0.00"

    abs_v = abs(v)

    if abs_v < 0.0001:
        return "0.00"
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


def get_value_color(current_value, previous_value=None, is_positive_only=False):
    """
    Determine color class for a value based on comparison with previous value.
    Returns: "value-up" (green), "value-down" (red), or "" (white/no color)
    
    For ALL values (volume, vdelta, ticks, volatility, OI):
    - Green if current > previous
    - Red if current < previous
    - White if no previous value or equal
    
    Changed: Vdelta now works like Volume - only shows color when comparing with previous value.
    """
    if current_value is None:
        return ""
    
    try:
        current = float(current_value)
    except (ValueError, TypeError):
        return ""
    
    # If we have previous value, compare
    if previous_value is not None:
        try:
            previous = float(previous_value)
            diff = current - previous
            if diff > 0.0001:
                return "value-up"
            elif diff < -0.0001:
                return "value-down"
            # If values are equal or very close, no color
            return ""
        except (ValueError, TypeError):
            pass
    
    # No previous value - no color (white) for all values
    # This makes vdelta work like volume - only color when comparing
    return ""

