from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from accounts.decorators import access_required

from screener.models import ScreenerSnapshot, Symbol
from screener.utils import format_volume, format_vdelta, get_value_color
from screener.templatetags.formatting import format_price, format_ticks


@access_required
def screener_list_api(request):
    from django.db import connection
    from django.utils import timezone
    from datetime import timedelta
    
    market_type = request.GET.get("market_type", "spot").strip()
    if market_type not in ["spot", "futures"]:
        market_type = "spot"
    
    recent_cutoff = timezone.now() - timedelta(hours=2)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT ON (s.symbol_id)
                s.id
            FROM screener_screenersnapshot s
            INNER JOIN screener_symbol sym ON s.symbol_id = sym.id
            WHERE s.ts >= %s AND sym.market_type = %s
            ORDER BY s.symbol_id, s.ts DESC
        """, [recent_cutoff, market_type])
        
        snapshot_ids = [row[0] for row in cursor.fetchall()]
    
    if not snapshot_ids:
        snapshot_ids = [0]
    
    qs = ScreenerSnapshot.objects.filter(id__in=snapshot_ids).select_related("symbol")
    
    search = request.GET.get("search", "").strip()
    if search:
        qs = qs.filter(symbol__symbol__icontains=search)

    def _to_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    vmin = _to_float(request.GET.get("min_volume_15m", "").strip())
    if vmin is not None:
        qs = qs.filter(volume_15m__gte=vmin)
    vmax = _to_float(request.GET.get("max_volume_15m", "").strip())
    if vmax is not None:
        qs = qs.filter(volume_15m__lte=vmax)

    cmin = _to_float(request.GET.get("min_change_15m", "").strip())
    if cmin is not None:
        qs = qs.filter(change_15m__gte=cmin)
    cmax = _to_float(request.GET.get("max_change_15m", "").strip())
    if cmax is not None:
        qs = qs.filter(change_15m__lte=cmax)

    oimin = _to_float(request.GET.get("min_oi_change_15m", "").strip())
    if oimin is not None:
        qs = qs.filter(oi_change_15m__gte=oimin)

    oi_min = _to_float(request.GET.get("min_open_interest", "").strip())
    if oi_min is not None:
        qs = qs.filter(open_interest__gte=oi_min)
    oi_max = _to_float(request.GET.get("max_open_interest", "").strip())
    if oi_max is not None:
        qs = qs.filter(open_interest__lte=oi_max)

    fmin = _to_float(request.GET.get("min_funding_rate", "").strip())
    if fmin is not None:
        qs = qs.filter(funding_rate__gte=fmin)
    fmax = _to_float(request.GET.get("max_funding_rate", "").strip())
    if fmax is not None:
        qs = qs.filter(funding_rate__lte=fmax)

    sort = request.GET.get("sort", "volume_15m")
    order = request.GET.get("order", "desc")

    allowed_sort_fields = {
        "symbol": "symbol__symbol",
        "price": "price",
        "change_5m": "change_5m",
        "change_15m": "change_15m",
        "change_1h": "change_1h",
        "change_8h": "change_8h",
        "change_1d": "change_1d",
        "oi_change_5m": "oi_change_5m",
        "oi_change_15m": "oi_change_15m",
        "oi_change_1h": "oi_change_1h",
        "oi_change_8h": "oi_change_8h",
        "oi_change_1d": "oi_change_1d",
        "volatility_5m": "volatility_5m",
        "volatility_15m": "volatility_15m",
        "volatility_1h": "volatility_1h",
        "ticks_5m": "ticks_5m",
        "ticks_15m": "ticks_15m",
        "ticks_1h": "ticks_1h",
        "vdelta_5m": "vdelta_5m",
        "vdelta_15m": "vdelta_15m",
        "vdelta_1h": "vdelta_1h",
        "vdelta_8h": "vdelta_8h",
        "vdelta_1d": "vdelta_1d",
        "volume_5m": "volume_5m",
        "volume_15m": "volume_15m",
        "volume_1h": "volume_1h",
        "volume_8h": "volume_8h",
        "volume_1d": "volume_1d",
        "funding_rate": "funding_rate",
        "open_interest": "open_interest",
        "ts": "ts",
    }

    sort_field = allowed_sort_fields.get(sort, "oi_change_15m")
    if order == "asc":
        qs = qs.order_by(sort_field)
    else:
        qs = qs.order_by(f"-{sort_field}")

    # Convert queryset to list
    snapshots = list(qs)
    
    # Store previous values per symbol for comparison
    # This will be populated as we iterate
    symbol_previous_values = {}
    
    data = []
    for s in snapshots:
        symbol = s.symbol.symbol
        prev_vals = symbol_previous_values.get(symbol, {})
        
        # Format vdelta values (use different thresholds for spot / futures)
        market_type = s.symbol.market_type
        vdelta_5m_formatted = format_vdelta(s.vdelta_5m, market_type)
        vdelta_15m_formatted = format_vdelta(s.vdelta_15m, market_type)
        vdelta_1h_formatted = format_vdelta(s.vdelta_1h, market_type)
        vdelta_8h_formatted = format_vdelta(s.vdelta_8h, market_type)
        vdelta_1d_formatted = format_vdelta(s.vdelta_1d, market_type)
        
        # Get colors for vdelta (compare with previous value for same symbol)
        vdelta_5m_color = get_value_color(s.vdelta_5m, prev_vals.get("vdelta_5m"), False)
        vdelta_15m_color = get_value_color(s.vdelta_15m, prev_vals.get("vdelta_15m"), False)
        vdelta_1h_color = get_value_color(s.vdelta_1h, prev_vals.get("vdelta_1h"), False)
        vdelta_8h_color = get_value_color(s.vdelta_8h, prev_vals.get("vdelta_8h"), False)
        vdelta_1d_color = get_value_color(s.vdelta_1d, prev_vals.get("vdelta_1d"), False)
        
        # Format volume values (use different thresholds for spot / futures)
        volume_5m_formatted = format_volume(s.volume_5m, market_type)
        volume_15m_formatted = format_volume(s.volume_15m, market_type)
        volume_1h_formatted = format_volume(s.volume_1h, market_type)
        volume_8h_formatted = format_volume(s.volume_8h, market_type)
        volume_1d_formatted = format_volume(s.volume_1d, market_type)
        
        # Get colors for volume (compare with previous value for same symbol)
        volume_5m_color = get_value_color(s.volume_5m, prev_vals.get("volume_5m"), True)
        volume_15m_color = get_value_color(s.volume_15m, prev_vals.get("volume_15m"), True)
        volume_1h_color = get_value_color(s.volume_1h, prev_vals.get("volume_1h"), True)
        volume_8h_color = get_value_color(s.volume_8h, prev_vals.get("volume_8h"), True)
        volume_1d_color = get_value_color(s.volume_1d, prev_vals.get("volume_1d"), True)
        
        # Format OI and get color (same thresholds as volume)
        oi_formatted = format_volume(s.open_interest, market_type)
        oi_color = get_value_color(s.open_interest, prev_vals.get("open_interest"), True)
        
        # Format price
        price_formatted = format_price(s.price)
        price_color = get_value_color(s.price, prev_vals.get("price"), True)
        
        # Format ticks
        ticks_5m_formatted = format_ticks(s.ticks_5m)
        ticks_15m_formatted = format_ticks(s.ticks_15m)
        ticks_1h_formatted = format_ticks(s.ticks_1h)
        ticks_5m_color = get_value_color(s.ticks_5m, prev_vals.get("ticks_5m"), True)
        ticks_15m_color = get_value_color(s.ticks_15m, prev_vals.get("ticks_15m"), True)
        ticks_1h_color = get_value_color(s.ticks_1h, prev_vals.get("ticks_1h"), True)
        
        data.append({
            "symbol": s.symbol.symbol,
            "name": s.symbol.name,
            "price": float(s.price),
            "price_formatted": price_formatted,
            "price_color": price_color,
            "change_5m": s.change_5m,
            "change_15m": s.change_15m,
            "change_1h": s.change_1h,
            "change_8h": s.change_8h,
            "change_1d": s.change_1d,
            "oi_change_5m": s.oi_change_5m,
            "oi_change_15m": s.oi_change_15m,
            "oi_change_1h": s.oi_change_1h,
            "oi_change_8h": s.oi_change_8h,
            "oi_change_1d": s.oi_change_1d,
            "volatility_5m": s.volatility_5m,
            "volatility_15m": s.volatility_15m,
            "volatility_1h": s.volatility_1h,
            "ticks_5m": s.ticks_5m,
            "ticks_5m_formatted": ticks_5m_formatted,
            "ticks_5m_color": ticks_5m_color,
            "ticks_15m": s.ticks_15m,
            "ticks_15m_formatted": ticks_15m_formatted,
            "ticks_15m_color": ticks_15m_color,
            "ticks_1h": s.ticks_1h,
            "ticks_1h_formatted": ticks_1h_formatted,
            "ticks_1h_color": ticks_1h_color,
            # Vdelta - raw values and formatted
            "vdelta_5m": s.vdelta_5m,
            "vdelta_5m_formatted": vdelta_5m_formatted,
            "vdelta_5m_color": vdelta_5m_color,
            "vdelta_15m": s.vdelta_15m,
            "vdelta_15m_formatted": vdelta_15m_formatted,
            "vdelta_15m_color": vdelta_15m_color,
            "vdelta_1h": s.vdelta_1h,
            "vdelta_1h_formatted": vdelta_1h_formatted,
            "vdelta_1h_color": vdelta_1h_color,
            "vdelta_8h": s.vdelta_8h,
            "vdelta_8h_formatted": vdelta_8h_formatted,
            "vdelta_8h_color": vdelta_8h_color,
            "vdelta_1d": s.vdelta_1d,
            "vdelta_1d_formatted": vdelta_1d_formatted,
            "vdelta_1d_color": vdelta_1d_color,
            # Volume - raw values and formatted
            "volume_5m": s.volume_5m,
            "volume_5m_formatted": volume_5m_formatted,
            "volume_5m_color": volume_5m_color,
            "volume_15m": s.volume_15m,
            "volume_15m_formatted": volume_15m_formatted,
            "volume_15m_color": volume_15m_color,
            "volume_1h": s.volume_1h,
            "volume_1h_formatted": volume_1h_formatted,
            "volume_1h_color": volume_1h_color,
            "volume_8h": s.volume_8h,
            "volume_8h_formatted": volume_8h_formatted,
            "volume_8h_color": volume_8h_color,
            "volume_1d": s.volume_1d,
            "volume_1d_formatted": volume_1d_formatted,
            "volume_1d_color": volume_1d_color,
            "funding_rate": float(s.funding_rate) if s.funding_rate else 0.0,
            "open_interest": float(s.open_interest) if s.open_interest else 0.0,
            "open_interest_formatted": oi_formatted,
            "open_interest_color": oi_color,
            "ts": s.ts.isoformat(),
        })
        
        # Store current values as previous for next update (for same symbol)
        symbol_previous_values[symbol] = {
            "price": float(s.price) if s.price is not None else None,
            "vdelta_5m": float(s.vdelta_5m) if s.vdelta_5m is not None else None,
            "vdelta_15m": float(s.vdelta_15m) if s.vdelta_15m is not None else None,
            "vdelta_1h": float(s.vdelta_1h) if s.vdelta_1h is not None else None,
            "vdelta_8h": float(s.vdelta_8h) if s.vdelta_8h is not None else None,
            "vdelta_1d": float(s.vdelta_1d) if s.vdelta_1d is not None else None,
            "volume_5m": float(s.volume_5m) if s.volume_5m is not None else None,
            "volume_15m": float(s.volume_15m) if s.volume_15m is not None else None,
            "volume_1h": float(s.volume_1h) if s.volume_1h is not None else None,
            "volume_8h": float(s.volume_8h) if s.volume_8h is not None else None,
            "volume_1d": float(s.volume_1d) if s.volume_1d is not None else None,
            "open_interest": float(s.open_interest) if s.open_interest is not None else None,
            "ticks_5m": float(s.ticks_5m) if s.ticks_5m is not None else None,
            "ticks_15m": float(s.ticks_15m) if s.ticks_15m is not None else None,
            "ticks_1h": float(s.ticks_1h) if s.ticks_1h is not None else None,
        }
    
    return JsonResponse(data, safe=False)


@access_required
def symbol_detail_api(request, symbol):
    market_type = request.GET.get("market_type", "spot").strip()
    if market_type not in ["spot", "futures"]:
        market_type = "spot"
    
    symbol_obj = get_object_or_404(
        Symbol,
        symbol__iexact=symbol,
        market_type=market_type
    )
    snapshots_qs = (
        ScreenerSnapshot.objects.filter(symbol=symbol_obj)
        .order_by("-ts")[:50]
        .select_related("symbol")
    )

    snapshots = [
        {
            "ts": s.ts.isoformat(),
            "price": float(s.price),
            "volatility_15m": s.volatility_15m,
            "volatility_5m": s.volatility_5m,
            "volatility_1h": s.volatility_1h,
            "ticks_15m": s.ticks_15m,
            "ticks_5m": s.ticks_5m,
            "ticks_1h": s.ticks_1h,
            "vdelta_5m": s.vdelta_5m,
            "vdelta_15m": s.vdelta_15m,
            "vdelta_1h": s.vdelta_1h,
            "vdelta_8h": s.vdelta_8h,
            "vdelta_1d": s.vdelta_1d,
            "volume_5m": s.volume_5m,
            "volume_15m": s.volume_15m,
            "volume_1h": s.volume_1h,
            "volume_8h": s.volume_8h,
            "volume_1d": s.volume_1d,
            "oi_change_5m": s.oi_change_5m,
            "oi_change_15m": s.oi_change_15m,
            "oi_change_1h": s.oi_change_1h,
            "oi_change_8h": s.oi_change_8h,
            "oi_change_1d": s.oi_change_1d,
            "change_5m": s.change_5m,
            "change_15m": s.change_15m,
            "change_1h": s.change_1h,
            "change_8h": s.change_8h,
            "change_1d": s.change_1d,
            "funding_rate": s.funding_rate,
            "open_interest": float(s.open_interest) if s.open_interest else 0.0,
        }
        for s in snapshots_qs
    ]

    latest = snapshots[0] if snapshots else None

    data = {
        "symbol": symbol_obj.symbol,
        "name": symbol_obj.name,
        "latest": latest,
        "snapshots": snapshots,
    }
    return JsonResponse(data)


@access_required
def symbols_list_api(request):
    """API для получения списка доступных символов."""
    from django.db import connection
    from django.utils import timezone
    from datetime import timedelta
    
    market_type = request.GET.get("market_type", "spot").strip()
    if market_type not in ["spot", "futures"]:
        market_type = "spot"
    
    search = request.GET.get("search", "").strip()
    
    # Получаем только символы, у которых есть свежие данные (за последние 2 часа)
    recent_cutoff = timezone.now() - timedelta(hours=2)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT sym.symbol, sym.name
            FROM screener_symbol sym
            INNER JOIN screener_screenersnapshot s ON s.symbol_id = sym.id
            WHERE s.ts >= %s AND sym.market_type = %s
        """, [recent_cutoff, market_type])
        
        symbols = [{"symbol": row[0], "name": row[1] or ""} for row in cursor.fetchall()]
    
    # Фильтрация по поисковому запросу
    if search:
        search_upper = search.upper()
        symbols = [s for s in symbols if search_upper in s["symbol"].upper() or (s["name"] and search_upper in s["name"].upper())]
    
    # Сортировка по символу
    symbols.sort(key=lambda x: x["symbol"])
    
    return JsonResponse({"symbols": symbols})


