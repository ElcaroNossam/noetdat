"""
Binance Spot ingest script for continuous updates.

Fetches spot symbols and metrics from Binance Spot API and writes them into
the PostgreSQL database via Django ORM.

This version runs continuously, updating data every second.

Run from the project root:

    python scripts/binance_spot_ingest.py
"""

import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

import django
import requests


def setup_django() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")


def fetch_tickers() -> List[Dict[str, Any]]:
    resp = requests.get(f"{BINANCE_BASE_URL}/api/v3/ticker/24hr", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [item for item in data if item.get("symbol", "").endswith("USDT")]


def ingest_snapshot() -> int:
    """Ingest one snapshot of all spot symbols. Returns count of symbols processed."""
    from screener.models import ScreenerSnapshot, Symbol

    tickers = fetch_tickers()
    now = datetime.now(timezone.utc)
    processed = 0

    for t in tickers:
        try:
            symbol_code = t["symbol"]

            last_price = Decimal(t.get("lastPrice", "0"))
            price_change_percent_24h = float(t.get("priceChangePercent", 0.0))
            # Use quoteVolume (volume in USDT) for spot
            volume_24h = float(t.get("quoteVolume", t.get("volume", 0.0)))

            # Calculate approximations based on 24h data
            change_5m = price_change_percent_24h / 288.0
            change_15m = price_change_percent_24h / 96.0
            change_1h = price_change_percent_24h / 24.0
            change_8h = price_change_percent_24h / 3.0
            change_1d = price_change_percent_24h

            volume_5m = volume_24h / 288.0
            volume_15m = volume_24h / 96.0
            volume_1h = volume_24h / 24.0
            volume_8h = volume_24h / 3.0
            volume_1d = volume_24h

            volatility_5m = abs(change_5m)
            volatility_15m = abs(change_15m)
            volatility_1h = abs(change_1h)

            ticks_5m = int(volume_5m / 1000.0)
            ticks_15m = int(volume_15m / 1000.0)
            ticks_1h = int(volume_1h / 1000.0)

            # Vdelta approximation: use timeframe-specific change with 24h volume
            # For spot: no division (multiply by 100 for better readability)
            # Formula: vdelta_tf = change_tf * volume_24h
            # This ensures correct ratio between timeframes (1d/5m = 288, not 288²)
            vdelta_5m = change_5m * volume_24h
            vdelta_15m = change_15m * volume_24h
            vdelta_1h = change_1h * volume_24h
            vdelta_8h = change_8h * volume_24h
            vdelta_1d = change_1d * volume_24h

            # Spot doesn't have open interest or funding rate, but we'll get it from futures
            # Get OI from futures for the same symbol
            futures_symbol = Symbol.objects.filter(
                symbol=symbol_code, market_type="futures"
            ).first()
            
            # Initialize OI and funding rate
            oi = 0.0
            funding_rate = 0.0
            oi_change_5m = 0.0
            oi_change_15m = 0.0
            oi_change_1h = 0.0
            oi_change_8h = 0.0
            oi_change_1d = 0.0
            
            futures_snapshot = None
            if futures_symbol:
                # Get latest futures snapshot to get OI, funding rate, and OI changes
                futures_snapshot = (
                    ScreenerSnapshot.objects.filter(symbol=futures_symbol)
                    .order_by("-ts")
                    .first()
                )
                if futures_snapshot:
                    oi = float(futures_snapshot.open_interest) if futures_snapshot.open_interest else 0.0
                    funding_rate = float(futures_snapshot.funding_rate) if futures_snapshot.funding_rate else 0.0
                    # Get OI changes directly from futures snapshot
                    oi_change_5m = float(futures_snapshot.oi_change_5m) if futures_snapshot.oi_change_5m else 0.0
                    oi_change_15m = float(futures_snapshot.oi_change_15m) if futures_snapshot.oi_change_15m else 0.0
                    oi_change_1h = float(futures_snapshot.oi_change_1h) if futures_snapshot.oi_change_1h else 0.0
                    oi_change_8h = float(futures_snapshot.oi_change_8h) if futures_snapshot.oi_change_8h else 0.0
                    oi_change_1d = float(futures_snapshot.oi_change_1d) if futures_snapshot.oi_change_1d else 0.0

            # Get or create symbol with market_type="spot"
            # Use filter().first() + create() to avoid race conditions
            symbol_obj = Symbol.objects.filter(
                symbol=symbol_code, market_type="spot"
            ).first()
            if not symbol_obj:
                symbol_obj = Symbol.objects.create(
                    symbol=symbol_code,
                    market_type="spot",
                    name=symbol_code,
                )

            ScreenerSnapshot.objects.create(
                symbol=symbol_obj,
                ts=now,
                price=last_price,
                open_interest=oi,
                funding_rate=funding_rate,
                change_5m=change_5m,
                change_15m=change_15m,
                change_1h=change_1h,
                change_8h=change_8h,
                change_1d=change_1d,
                oi_change_5m=oi_change_5m,
                oi_change_15m=oi_change_15m,
                oi_change_1h=oi_change_1h,
                oi_change_8h=oi_change_8h,
                oi_change_1d=oi_change_1d,
                volatility_5m=volatility_5m,
                volatility_15m=volatility_15m,
                volatility_1h=volatility_1h,
                ticks_5m=ticks_5m,
                ticks_15m=ticks_15m,
                ticks_1h=ticks_1h,
                vdelta_5m=vdelta_5m,
                vdelta_15m=vdelta_15m,
                vdelta_1h=vdelta_1h,
                vdelta_8h=vdelta_8h,
                vdelta_1d=vdelta_1d,
                volume_5m=volume_5m,
                volume_15m=volume_15m,
                volume_1h=volume_1h,
                volume_8h=volume_8h,
                volume_1d=volume_1d,
            )
            processed += 1
        except Exception as e:
            print(f"Error processing {t.get('symbol', 'unknown')}: {e}")
            continue

    return processed


def main() -> None:
    setup_django()
    
    print("Starting Binance Spot ingest loop (updates every 1 second)...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            start_time = time.time()
            count = ingest_snapshot()
            elapsed = time.time() - start_time
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ingested {count} spot symbols in {elapsed:.2f}s")
            
            sleep_time = max(0, 5.0 - elapsed)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()

