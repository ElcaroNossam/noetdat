from django.contrib import admin

from .models import AlertRule


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = (
        "symbol",
        "metric",
        "operator",
        "threshold",
        "telegram_chat_id",
        "active",
        "last_triggered_at",
    )
    list_filter = ("active", "metric", "symbol")
    search_fields = ("symbol__symbol", "telegram_chat_id")


