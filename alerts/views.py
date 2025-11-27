from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from screener.models import Symbol

from .forms import AlertRuleForm
from .models import AlertRule


@login_required
def create_alert(request, symbol):
    market_type = request.GET.get("market_type", "futures").strip()
    if market_type not in ["spot", "futures"]:
        market_type = "futures"
    
    symbol_obj = get_object_or_404(
        Symbol,
        symbol__iexact=symbol,
        market_type=market_type
    )

    if request.method == "POST":
        form = AlertRuleForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.symbol = symbol_obj
            alert.save()
            messages.success(request, "Alert rule created.")
            from django.urls import reverse
            url = reverse("screener:symbol_detail", args=[symbol_obj.symbol])
            return redirect(f"{url}?market_type={market_type}")
    else:
        form = AlertRuleForm()

    return render(
        request,
        "alerts/alert_form.html",
        {
            "symbol": symbol_obj,
            "form": form,
            "market_type": market_type,
        },
    )


@login_required
def alert_list(request):
    """Страница управления алертами пользователя."""
    alerts = AlertRule.objects.filter(user=request.user).select_related("symbol").order_by("-created_at")
    
    market_type = request.GET.get("market_type", "").strip()
    if market_type in ["spot", "futures"]:
        alerts = alerts.filter(symbol__market_type=market_type)
    
    search = request.GET.get("search", "").strip()
    if search:
        alerts = alerts.filter(symbol__symbol__icontains=search)
    
    active_filter = request.GET.get("active", "").strip()
    if active_filter == "true":
        alerts = alerts.filter(active=True)
    elif active_filter == "false":
        alerts = alerts.filter(active=False)
    
    context = {
        "alerts": alerts,
        "market_type": market_type,
        "search": search,
        "active_filter": active_filter,
    }
    return render(request, "alerts/alert_list.html", context)


@login_required
def edit_alert(request, alert_id):
    """Редактирование алерта."""
    alert = get_object_or_404(AlertRule, id=alert_id, user=request.user)
    
    if request.method == "POST":
        form = AlertRuleForm(request.POST, instance=alert)
        if form.is_valid():
            form.save()
            messages.success(request, "Alert rule updated.")
            return redirect("alerts:list")
    else:
        form = AlertRuleForm(instance=alert)
    
    context = {
        "alert": alert,
        "form": form,
    }
    return render(request, "alerts/alert_edit.html", context)


@login_required
@require_POST
def delete_alert(request, alert_id):
    """Удаление алерта."""
    alert = get_object_or_404(AlertRule, id=alert_id, user=request.user)
    alert.delete()
    messages.success(request, "Alert rule deleted.")
    return redirect("alerts:list")


@login_required
@require_POST
def toggle_alert(request, alert_id):
    """Включение/выключение алерта."""
    alert = get_object_or_404(AlertRule, id=alert_id, user=request.user)
    alert.active = not alert.active
    alert.save()
    messages.success(request, f"Alert rule {'activated' if alert.active else 'deactivated'}.")
    return redirect("alerts:list")


