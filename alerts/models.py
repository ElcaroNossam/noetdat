from django.conf import settings
from django.db import models

from screener.models import Symbol


class AlertRule(models.Model):
    METRIC_CHOICES = [
        ("change_15m", "Price change 15m, %"),
        ("change_1h", "Price change 1h, %"),
        ("change_1d", "Price change 1d, %"),
        ("oi_change_15m", "OI change 15m, %"),
        ("oi_change_1h", "OI change 1h, %"),
        ("volume_15m", "Volume 15m"),
        ("volume_1h", "Volume 1h"),
        ("funding_rate", "Funding rate"),
        ("vdelta_15m", "Vdelta 15m"),
    ]

    OPERATOR_CHOICES = [
        (">", ">"),
        ("<", "<"),
        (">=", ">="),
        ("<=", "<="),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alert_rules",
        null=True,
        blank=True,
    )
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name="alerts")

    metric = models.CharField(max_length=32, choices=METRIC_CHOICES)
    operator = models.CharField(max_length=2, choices=OPERATOR_CHOICES)
    threshold = models.FloatField()

    telegram_chat_id = models.BigIntegerField(
        help_text="Telegram chat id to send alerts to", null=True, blank=True
    )

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.symbol.symbol} {self.metric} {self.operator} {self.threshold}"


