from django.db import models


class Symbol(models.Model):
    MARKET_TYPE_CHOICES = [
        ("spot", "Spot"),
        ("futures", "Futures"),
    ]
    
    symbol = models.CharField(max_length=20)  # BTCUSDT (not unique alone, unique with market_type)
    name = models.CharField(max_length=50, blank=True)
    market_type = models.CharField(
        max_length=10, choices=MARKET_TYPE_CHOICES, default="futures"
    )

    class Meta:
        unique_together = [["symbol", "market_type"]]

    def __str__(self) -> str:
        return self.symbol


class ScreenerSnapshot(models.Model):
    symbol = models.ForeignKey(
        Symbol, on_delete=models.CASCADE, related_name="snapshots"
    )
    ts = models.DateTimeField(db_index=True)

    # Core price/open interest/funding
    price = models.DecimalField(max_digits=20, decimal_places=8)
    open_interest = models.FloatField(default=0.0)
    funding_rate = models.FloatField(default=0.0)

    # Price change (%)
    change_5m = models.FloatField(default=0.0)
    change_15m = models.FloatField(default=0.0)
    change_1h = models.FloatField(default=0.0)
    change_8h = models.FloatField(default=0.0)
    change_1d = models.FloatField(default=0.0)

    # OI change (%)
    oi_change_5m = models.FloatField(default=0.0)
    oi_change_15m = models.FloatField(default=0.0)
    oi_change_1h = models.FloatField(default=0.0)
    oi_change_8h = models.FloatField(default=0.0)
    oi_change_1d = models.FloatField(default=0.0)

    # Volatility
    volatility_5m = models.FloatField(default=0.0)
    volatility_15m = models.FloatField(default=0.0)
    volatility_1h = models.FloatField(default=0.0)

    # Ticks
    ticks_5m = models.IntegerField(default=0)
    ticks_15m = models.IntegerField(default=0)
    ticks_1h = models.IntegerField(default=0)

    # Vdelta
    vdelta_5m = models.FloatField(default=0.0)
    vdelta_15m = models.FloatField(default=0.0)
    vdelta_1h = models.FloatField(default=0.0)
    vdelta_8h = models.FloatField(default=0.0)
    vdelta_1d = models.FloatField(default=0.0)

    # Volume
    volume_5m = models.FloatField(default=0.0)
    volume_15m = models.FloatField(default=0.0)
    volume_1h = models.FloatField(default=0.0)
    volume_8h = models.FloatField(default=0.0)
    volume_1d = models.FloatField(default=0.0)

    class Meta:
        indexes = [
            models.Index(fields=["symbol", "-ts"]),
        ]

    def __str__(self) -> str:
        return f"{self.symbol.symbol} @ {self.ts}"


