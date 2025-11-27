from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from accounts.decorators import access_required

from .models import ScreenerSnapshot, Symbol


@access_required
def screener_list(request):
    """Main screener view showing the latest snapshot per symbol with filters and sorting."""

    from django.db import connection
    from django.utils import timezone
    from datetime import timedelta
    
    market_type = request.GET.get("market_type", "futures").strip()
    if market_type not in ["spot", "futures"]:
        market_type = "futures"
    
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

    # Extended filters
    min_volume_15m = request.GET.get("min_volume_15m", "").strip()
    max_volume_15m = request.GET.get("max_volume_15m", "").strip()
    min_change_15m = request.GET.get("min_change_15m", "").strip()
    max_change_15m = request.GET.get("max_change_15m", "").strip()
    min_oi_change_15m = request.GET.get("min_oi_change_15m", "").strip()
    min_open_interest = request.GET.get("min_open_interest", "").strip()
    max_open_interest = request.GET.get("max_open_interest", "").strip()
    min_funding_rate = request.GET.get("min_funding_rate", "").strip()
    max_funding_rate = request.GET.get("max_funding_rate", "").strip()

    def _to_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return None

    vmin = _to_float(min_volume_15m)
    if vmin is not None:
        qs = qs.filter(volume_15m__gte=vmin)
    vmax = _to_float(max_volume_15m)
    if vmax is not None:
        qs = qs.filter(volume_15m__lte=vmax)

    cmin = _to_float(min_change_15m)
    if cmin is not None:
        qs = qs.filter(change_15m__gte=cmin)
    cmax = _to_float(max_change_15m)
    if cmax is not None:
        qs = qs.filter(change_15m__lte=cmax)

    oimin = _to_float(min_oi_change_15m)
    if oimin is not None:
        qs = qs.filter(oi_change_15m__gte=oimin)

    oi_min = _to_float(min_open_interest)
    if oi_min is not None:
        qs = qs.filter(open_interest__gte=oi_min)
    oi_max = _to_float(max_open_interest)
    if oi_max is not None:
        qs = qs.filter(open_interest__lte=oi_max)

    fmin = _to_float(min_funding_rate)
    if fmin is not None:
        qs = qs.filter(funding_rate__gte=fmin)
    fmax = _to_float(max_funding_rate)
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

    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search": search,
        "market_type": market_type,
        "min_volume_15m": min_volume_15m,
        "max_volume_15m": max_volume_15m,
        "min_change_15m": min_change_15m,
        "max_change_15m": max_change_15m,
        "min_oi_change_15m": min_oi_change_15m,
        "min_open_interest": min_open_interest,
        "max_open_interest": max_open_interest,
        "min_funding_rate": min_funding_rate,
        "max_funding_rate": max_funding_rate,
        "sort": sort,
        "order": order,
        "allowed_sort_fields": allowed_sort_fields,
    }
    return render(request, "screener/screener_list.html", context)


@access_required
def symbol_detail(request, symbol):
    market_type = request.GET.get("market_type", "futures").strip()
    if market_type not in ["spot", "futures"]:
        market_type = "futures"
    
    symbol_obj = get_object_or_404(
        Symbol, 
        symbol__iexact=symbol,
        market_type=market_type
    )
    snapshots = (
        ScreenerSnapshot.objects.filter(symbol=symbol_obj)
        .order_by("-ts")[:50]
        .select_related("symbol")
    )
    snapshots = list(snapshots)
    latest_snapshot = snapshots[0] if snapshots else None

    context = {
        "symbol": symbol_obj,
        "latest_snapshot": latest_snapshot,
        "snapshots": snapshots,
        "market_type": market_type,
    }
    return render(request, "screener/symbol_detail.html", context)


@access_required
def trading_terminal(request, symbol):
    """Торговый терминал с графиком."""
    market_type = request.GET.get("market_type", "futures").strip()
    if market_type not in ["spot", "futures"]:
        market_type = "futures"
    
    symbol_obj = get_object_or_404(
        Symbol,
        symbol__iexact=symbol,
        market_type=market_type
    )
    
    snapshots = (
        ScreenerSnapshot.objects.filter(symbol=symbol_obj)
        .order_by("-ts")[:100]
        .select_related("symbol")
    )
    snapshots = list(snapshots)
    latest_snapshot = snapshots[0] if snapshots else None

    context = {
        "symbol": symbol_obj,
        "latest_snapshot": latest_snapshot,
        "snapshots": snapshots,
        "market_type": market_type,
    }
    return render(request, "screener/trading_terminal.html", context)


