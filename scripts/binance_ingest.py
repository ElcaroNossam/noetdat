"""
Simple Binance Futures USDT-margined ingest script with continuous updates.

Fetches symbols and basic metrics from Binance public API and writes them into
the PostgreSQL database via Django ORM.

This version runs continuously, updating data every second.

Run from the project root:

    python scripts/binance_ingest.py
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


BINANCE_BASE_URL = os.getenv("BINANCE_BASE_URL", "https://fapi.binance.com")


def fetch_tickers() -> List[Dict[str, Any]]:
    resp = requests.get(f"{BINANCE_BASE_URL}/fapi/v1/ticker/24hr", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return [item for item in data if item.get("symbol", "").endswith("USDT")]


def fetch_open_interest(symbol: str) -> float:
    try:
        resp = requests.get(
            f"{BINANCE_BASE_URL}/fapi/v1/openInterest",
            params={"symbol": symbol},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("openInterest", 0.0))
    except Exception:
        return 0.0


def fetch_funding_rate(symbol: str) -> float:
    """Fetch current funding rate for a symbol."""
    try:
        resp = requests.get(
            f"{BINANCE_BASE_URL}/fapi/v1/premiumIndex",
            params={"symbol": symbol},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return float(data.get("lastFundingRate", 0.0))
    except Exception:
        return 0.0


def ingest_snapshot() -> int:
    """Ingest one snapshot of all symbols. Returns count of symbols processed."""
    from screener.models import ScreenerSnapshot, Symbol

    tickers = fetch_tickers()
    now = datetime.now(timezone.utc)
    processed = 0

    for t in tickers:
        try:
            symbol_code = t["symbol"]

            last_price = Decimal(t.get("lastPrice", "0"))
            price_change_percent_24h = float(t.get("priceChangePercent", 0.0))
            # Use quoteVolume (volume in USDT) instead of volume (volume in base currency)
            # quoteVolume is the total volume in the quote currency (USDT)
            volume_24h = float(t.get("quoteVolume", t.get("volume", 0.0)))
            
            # Fetch funding rate from separate endpoint (more reliable)
            funding_rate = fetch_funding_rate(symbol_code)

            # Calculate approximations based on 24h data
            # Timeframe ratios: 5m=1/288, 15m=1/96, 1h=1/24, 8h=1/3, 1d=1
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

            # Approximate volatility as absolute change
            volatility_5m = abs(change_5m)
            volatility_15m = abs(change_15m)
            volatility_1h = abs(change_1h)

            # Approximate ticks based on volume (higher volume = more ticks)
            # Rough estimate: 1 tick per 1000 USDT volume
            ticks_5m = int(volume_5m / 1000.0)
            ticks_15m = int(volume_15m / 1000.0)
            ticks_1h = int(volume_1h / 1000.0)

            # Vdelta approximation: positive if price going up, negative if down
            # Use change as proxy
            vdelta_5m = change_5m * volume_5m / 100.0
            vdelta_15m = change_15m * volume_15m / 100.0
            vdelta_1h = change_1h * volume_1h / 100.0
            vdelta_8h = change_8h * volume_8h / 100.0
            vdelta_1d = change_1d * volume_1d / 100.0

            oi = fetch_open_interest(symbol_code)

            # Try to get previous snapshot to calculate OI changes
            # Get or create symbol with market_type="futures"
            # Use filter().first() + create() to avoid race conditions
            symbol_obj = Symbol.objects.filter(
                symbol=symbol_code, market_type="futures"
            ).first()
            if not symbol_obj:
                symbol_obj = Symbol.objects.create(
                    symbol=symbol_code,
                    market_type="futures",
                    name=symbol_code,
                )

            # Get previous snapshot if exists
            prev_snapshot = (
                ScreenerSnapshot.objects.filter(symbol=symbol_obj)
                .order_by("-ts")
                .first()
            )

            oi_change_5m = 0.0
            oi_change_15m = 0.0
            oi_change_1h = 0.0
            oi_change_8h = 0.0
            oi_change_1d = 0.0

            if prev_snapshot and prev_snapshot.open_interest > 0:
                oi_change_pct = ((oi - prev_snapshot.open_interest) / prev_snapshot.open_interest) * 100.0
                oi_change_5m = oi_change_pct / 288.0
                oi_change_15m = oi_change_pct / 96.0
                oi_change_1h = oi_change_pct / 24.0
                oi_change_8h = oi_change_pct / 3.0
                oi_change_1d = oi_change_pct

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
    
    print("Starting Binance ingest loop (updates every 1 second)...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            start_time = time.time()
            count = ingest_snapshot()
            elapsed = time.time() - start_time
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ingested {count} symbols in {elapsed:.2f}s")
            
            # Sleep to make it approximately 1 second between updates
            sleep_time = max(0, 5.0 - elapsed)
            time.sleep(sleep_time)
    except KeyboardInterrupt:
        print("\nStopped by user.")


if __name__ == "__main__":
    main()
