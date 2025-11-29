"""
Template filters for formatting numeric values, especially prices and volumes.
"""
from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def format_price(value):
    """
    Adaptive price formatting with K/M/B suffixes for large values:
    - >= 1B: show as X.XXB
    - >= 1M: show as X.XXM
    - >= 1K: show as X.XXK
    - >= 1: 2 decimal places (e.g., 51234.56)
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

    # For large prices, use K/M/B suffixes
    if abs_v >= 1_000_000_000:
        return f"{v / 1_000_000_000:.2f}B"
    elif abs_v >= 1_000_000:
        return f"{v / 1_000_000:.2f}M"
    elif abs_v >= 1_000:
        return f"{v / 1_000:.2f}K"
    elif abs_v >= 1:
        return f"{v:.2f}"
    elif abs_v >= 0.01:
        return f"{v:.4f}"
    else:
        return f"{v:.8f}"


@register.filter
def format_volume(value, market_type=None):
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

    # Different thresholds for spot vs futures to make spot volumes more readable.
    if market_type == "spot":
        k_threshold = 1_00  # start K earlier on spot (e.g. 100+)
        m_threshold = 500_000
        b_threshold = 1_000_000_000
    else:
        # Futures / default thresholds
        k_threshold = 1_000
        m_threshold = 1_000_000
        b_threshold = 1_000_000_000

    if abs_v >= b_threshold:
        return f"{v / 1_000_000_000:.2f}B"
    elif abs_v >= m_threshold:
        return f"{v / 1_000_000:.2f}M"
    elif abs_v >= k_threshold:
        return f"{v / 1_000:.2f}K"
    else:
        return f"{v:.2f}"


@register.filter
def format_vdelta(value, market_type=None):
    """
    Format volume delta with K/M/B suffixes and smart rounding.
    Thresholds can be slightly different for spot / futures to make values
    more readable on spot, where absolute numbers are usually smaller.
    Common logic:
    - abs(v) very small -> 0.00
    - large values -> K / M suffix
    - medium values -> integer or 1 decimal
    - small values -> 2 decimals
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

    # Для Vdelta делаем одинаковые пороги для spot и futures,
    # чтобы суффиксы вели себя одинаково на всех рынках.
    k_threshold = 1_000.0
    m_threshold = 1_000_000.0

    if abs_v >= m_threshold:
        return f"{v / 1_000_000:.2f}M"
    elif abs_v >= k_threshold:
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
    - >= 0.001: 4 decimals
    - < 0.001: 6 decimals (to show very small negative values)
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
    elif abs_v >= 0.001:
        return f"{v:.4f}"
    else:
        # For very small values, show more decimals to distinguish from zero
        return f"{v:.6f}"


@register.filter
def format_ticks(value):
    """
    Format ticks with K/M/B suffixes:
    - >= 1B: show as X.XXB
    - >= 1M: show as X.XXM
    - >= 1K: show as X.XXK
    - < 1K: show as integer
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
        return f"{int(v)}"

