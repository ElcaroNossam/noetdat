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


def send_telegram_message(token: str, chat_id: int, text: str, parse_mode: str = "HTML") -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            timeout=10
        )
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

        # Format value based on metric type
        def format_metric_value(metric_name: str, val: float) -> str:
            """Format metric value for display."""
            if "change" in metric_name or "oi_change" in metric_name:
                return f"{val:.2f}%"
            elif "volume" in metric_name:
                abs_v = abs(val)
                if abs_v >= 1_000_000_000:
                    return f"{val / 1_000_000_000:.2f}B"
                elif abs_v >= 1_000_000:
                    return f"{val / 1_000_000:.2f}M"
                elif abs_v >= 1_000:
                    return f"{val / 1_000:.2f}K"
                else:
                    return f"{val:.2f}"
            elif "funding" in metric_name:
                return f"{val:.4f}"
            else:
                return f"{val:.2f}"
        
        # Get metric display name
        metric_display = dict(alert.METRIC_CHOICES).get(alert.metric, alert.metric)
        
        # Format values
        threshold_formatted = format_metric_value(alert.metric, float(alert.threshold))
        value_formatted = format_metric_value(alert.metric, float(value))
        
        # Determine emoji based on operator and value
        if alert.operator in [">", ">="]:
            emoji = "📈" if float(value) > float(alert.threshold) else "📉"
        else:
            emoji = "📉" if float(value) < float(alert.threshold) else "📈"
        
        # Create beautiful HTML message
        text = (
            f"{emoji} <b>Алерт сработал!</b>\n\n"
            f"<b>Символ:</b> {alert.symbol.symbol}\n"
            f"<b>Тип рынка:</b> {alert.symbol.market_type.upper()}\n"
            f"<b>Показатель:</b> {metric_display}\n"
            f"<b>Условие:</b> {alert.metric} {alert.operator} {threshold_formatted}\n"
            f"<b>Текущее значение:</b> <code>{value_formatted}</code>\n"
            f"<b>Порог:</b> <code>{threshold_formatted}</code>\n\n"
            f"⏰ {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        )
        
        send_telegram_message(token, alert.telegram_chat_id, text)
        alert.last_triggered_at = now
        alert.save(update_fields=["last_triggered_at"])

    print("Alert check completed.")


if __name__ == "__main__":
    main()


