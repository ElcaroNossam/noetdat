from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from screener.models import Symbol

from .forms import AlertRuleForm


@login_required
def create_alert(request, symbol):
    symbol_obj = get_object_or_404(Symbol, symbol__iexact=symbol)

    if request.method == "POST":
        form = AlertRuleForm(request.POST)
        if form.is_valid():
            alert = form.save(commit=False)
            alert.user = request.user
            alert.symbol = symbol_obj
            alert.save()
            messages.success(request, "Alert rule created.")
            return redirect("screener:symbol_detail", symbol=symbol_obj.symbol)
    else:
        form = AlertRuleForm()

    return render(
        request,
        "alerts/alert_form.html",
        {
            "symbol": symbol_obj,
            "form": form,
        },
    )


