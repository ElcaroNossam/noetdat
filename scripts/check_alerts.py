"""
Periodic checker that evaluates AlertRule conditions against latest snapshots
and sends Telegram notifications when conditions are met.

Run from the project root (e.g. via cron every minute):

    TELEGRAM_BOT_TOKEN=... python scripts/check_alerts.py
"""

import datetime as dt
import os
import sys
from pathlib import Path
from typing import Callable

import django
import requests


def setup_django() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


def send_telegram_message(token: str, chat_id: int, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        print(f"Failed to send telegram message to {chat_id}: {exc}")


def main() -> None:
    setup_django()

    from alerts.models import AlertRule
    from screener.models import ScreenerSnapshot

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN env var is required")

    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    cooldown = dt.timedelta(minutes=5)

    operator_funcs: dict[str, Callable[[float, float], bool]] = {
        ">": lambda v, t: v > t,
        "<": lambda v, t: v < t,
        ">=": lambda v, t: v >= t,
        "<=": lambda v, t: v <= t,
    }

    for alert in AlertRule.objects.filter(active=True).select_related("symbol"):
        if not alert.telegram_chat_id:
            continue

        # Cooldown check
        if alert.last_triggered_at and now - alert.last_triggered_at < cooldown:
            continue

        snapshot = (
            ScreenerSnapshot.objects.filter(symbol=alert.symbol)
            .order_by("-ts")
            .first()
        )
        if not snapshot:
            continue

        value = getattr(snapshot, alert.metric, None)
        if value is None:
            continue

        op_func = operator_funcs.get(alert.operator)
        if not op_func:
            continue

        if not op_func(float(value), float(alert.threshold)):
            continue

        text = (
            f"Alert for {alert.symbol.symbol}: {alert.metric} "
            f"{alert.operator} {alert.threshold} (actual: {value})"
        )
        send_telegram_message(token, alert.telegram_chat_id, text)
        alert.last_triggered_at = now
        alert.save(update_fields=["last_triggered_at"])

    print("Alert check completed.")


if __name__ == "__main__":
    main()


