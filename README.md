# Noet-Dat

Minimal Django 5.x project for a crypto screener backed by PostgreSQL.

The project contains main apps:

- `accounts` — registration, login/logout, user profile (`Profile` with `is_pro` flag);
- `screener` — models and views for the HTML screener UI;
- `api` — JSON API mirroring the main screener filters and symbol details;
- `alerts` — alert rules for Telegram notifications.

## Requirements

- Python 3.10+
- PostgreSQL instance (local or remote)

Python dependencies are listed in `requirements.txt`, key ones:

- Django 5.x
- `psycopg2-binary` for PostgreSQL
- `requests` for Binance/Telegram HTTP calls
- `python-telegram-bot` for the helper bot

## Quick start

From the project root (`/home/illiateslenko/project/scan`):

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configure environment variables (example for local development):

```bash
export DJANGO_SECRET_KEY="dev-secret-key-change-me"
export DJANGO_DEBUG="True"
export DJANGO_ALLOWED_HOSTS="localhost,127.0.0.1"

export DB_NAME="screener_db"
export DB_USER="screener_user"
export DB_PASSWORD="password"
export DB_HOST="localhost"
export DB_PORT="5432"

export TELEGRAM_BOT_TOKEN="your-telegram-bot-token"
```

Create the database and user in PostgreSQL to match these values (or adjust env vars).

Apply migrations and create a superuser:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Run the development server:

```bash
python manage.py runserver
```

Now you have:

- `http://localhost:8000/` — main screener (HTML table);
- `http://localhost:8000/accounts/register/` — user registration;
- `http://localhost:8000/accounts/login/` — login;
- `http://localhost:8000/admin/` — Django admin;
- `http://localhost:8000/api/screener/` — JSON screener endpoint;
- `http://localhost:8000/api/symbol/BTCUSDT/` — JSON symbol details.

## Example data ingest (test)

There is a minimal example script that inserts one test symbol and one snapshot:

- `scripts/ingest_example.py`

Run it from the project root (after applying migrations and configuring DB/env):

```bash
python scripts/ingest_example.py
```

This will:

- call `django.setup()` for the `config.settings` module,
- create or get `Symbol(symbol="BTCUSDT")`,
- create a new `ScreenerSnapshot` row with sample metrics.

## Binance ingest

There is a simple ingest script that pulls all USDT-margined futures symbols from
Binance Futures (`fapi` API) and writes snapshots:

```bash
python scripts/binance_ingest.py
```

It fills:

- `price`, `change_1d`, `volume_1d` from `ticker/24hr`;
- approximates `change_15m`/`volume_15m` as fractions of 24h values;
- fetches current `open_interest` from `openInterest`;
- stores everything in `ScreenerSnapshot`.

For production, you can replace approximations with precise computations from
`/fapi/v1/klines` and additional logic.

## Telegram bot and alerts

There is a small helper bot that just tells the user their `chat_id`:

```bash
TELEGRAM_BOT_TOKEN=... python scripts/telegram_bot.py
```

Use `/start` in Telegram to get your `chat_id`, then paste it into the alert form
on a symbol detail page.

Alerts are defined by the `alerts.AlertRule` model, which stores:

- `symbol`, `metric`, `operator`, `threshold`;
- `telegram_chat_id` to send alerts to;
- `active`, `created_at`, `last_triggered_at`.

To periodically check alerts and send notifications, run (e.g. via cron every minute):

```bash
TELEGRAM_BOT_TOKEN=... python scripts/check_alerts.py
```

The checker:

- finds the latest `ScreenerSnapshot` for each active rule;
- evaluates the condition (e.g. `change_15m > 5`);
- sends a Telegram message when the condition is met, with a small cooldown.

## How to hook your own data collectors

External Python scripts (e.g. Binance collectors) should follow the same pattern:

1. Configure Django:

   ```python
   import os
   import django

   os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
   django.setup()
   ```

2. Import models:

   ```python
   from screener.models import Symbol, ScreenerSnapshot
   ```

3. For each symbol/interval:

   - create or update a `Symbol` instance;
   - append a `ScreenerSnapshot` instance with the latest metrics.

The web UI and API always show the most recent snapshot per symbol (using PostgreSQL
`DISTINCT ON` semantics under the hood), so you can simply keep pushing new rows.



