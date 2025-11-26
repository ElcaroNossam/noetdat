"""
Example standalone script that writes test data into the Django/PostgreSQL database.

Run from the project root:

    python scripts/ingest_example.py
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import django


def setup_django() -> None:
    """
    Configure Django so that we can use the ORM from a standalone script.
    Ensures the project root (where `config` lives) is on sys.path.
    """
    base_dir = Path(__file__).resolve().parent.parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


def main() -> None:
    setup_django()

    from screener.models import ScreenerSnapshot, Symbol

    symbol, _ = Symbol.objects.get_or_create(
        symbol="BTCUSDT",
        defaults={"name": "Bitcoin"},
    )

    ScreenerSnapshot.objects.create(
        symbol=symbol,
        ts=datetime.utcnow(),
        price=Decimal("50000"),
        volatility_15m=0.5,
        ticks_15m=100,
        ticks_5m=40,
        vdelta_1m=100000.0,
        vdelta_5m=500000.0,
        volume_5m=1000000.0,
        volume_1h=5000000.0,
        oi_change_5m=0.1,
        oi_change_15m=0.2,
        oi_change_1h=0.3,
        funding_rate=0.0005,
    )

    print("Test snapshot inserted for BTCUSDT")


if __name__ == "__main__":
    main()




