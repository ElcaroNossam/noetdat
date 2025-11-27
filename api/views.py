from django.db.models import Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from screener.models import ScreenerSnapshot, Symbol


def screener_list_api(request):
    from django.utils import timezone
    from datetime import timedelta
    
    recent_cutoff = timezone.now() - timedelta(hours=6)
    
    latest_per_symbol = (
        ScreenerSnapshot.objects
        .filter(ts__gte=recent_cutoff)
        .values("symbol_id")
        .annotate(max_ts=Max("ts"))
    )
    
    q_filter = Q()
    for item in latest_per_symbol:
        q_filter |= Q(symbol_id=item["symbol_id"], ts=item["max_ts"])
    
    qs = ScreenerSnapshot.objects.filter(q_filter).select_related("symbol")

    # Market type filter (spot/futures)
    market_type = request.GET.get("market_type", "futures").strip()
    if market_type in ["spot", "futures"]:
        qs = qs.filter(symbol__market_type=market_type)
    
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

    data = [
        {
            "symbol": s.symbol.symbol,
            "name": s.symbol.name,
            "price": float(s.price),
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
            "ticks_15m": s.ticks_15m,
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
            "funding_rate": float(s.funding_rate) if s.funding_rate else 0.0,
            "open_interest": float(s.open_interest) if s.open_interest else 0.0,
            "ts": s.ts.isoformat(),
        }
        for s in qs
    ]
    return JsonResponse(data, safe=False)


def symbol_detail_api(request, symbol):
    symbol_obj = get_object_or_404(Symbol, symbol__iexact=symbol)
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
            "ticks_15m": s.ticks_15m,
            "ticks_5m": s.ticks_5m,
            "vdelta_5m": s.vdelta_5m,
            "volume_5m": s.volume_5m,
            "volume_1h": s.volume_1h,
            "oi_change_5m": s.oi_change_5m,
            "oi_change_15m": s.oi_change_15m,
            "oi_change_1h": s.oi_change_1h,
            "funding_rate": s.funding_rate,
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


