# Инструкция по развертыванию на AWS сервере через Nginx

## Предварительные требования

- AWS EC2 инстанс с Ubuntu (20.04 или 22.04)
- Доступ по SSH к серверу
- Доменное имя (опционально, для SSL)

## Шаг 1: Подключение к серверу

```bash
ssh -i your-key.pem ubuntu@your-server-ip
```

## Шаг 2: Обновление системы

```bash
sudo apt update
sudo apt upgrade -y
```

## Шаг 3: Установка зависимостей

```bash
# Python и pip
sudo apt install -y python3 python3-pip python3-venv

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Nginx
sudo apt install -y nginx

# Git
sudo apt install -y git

# Дополнительные инструменты
sudo apt install -y build-essential libpq-dev
```

## Шаг 4: Настройка PostgreSQL

```bash
# Переключение на пользователя postgres
sudo -u postgres psql

# В PostgreSQL консоли:
CREATE DATABASE scan_db;
CREATE USER scan_user WITH PASSWORD 'your_secure_password';
ALTER ROLE scan_user SET client_encoding TO 'utf8';
ALTER ROLE scan_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE scan_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE scan_db TO scan_user;
\q
```

## Шаг 5: Клонирование репозитория

```bash
# Создание директории для приложений
sudo mkdir -p /var/www
cd /var/www

# Клонирование репозитория
sudo git clone https://github.com/your-username/your-repo-name.git scan
sudo chown -R $USER:$USER /var/www/scan
cd scan
```

## Шаг 6: Настройка виртуального окружения

```bash
# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

## Шаг 7: Настройка переменных окружения

```bash
# Создание .env файла
nano .env
```

Добавьте в `.env`:

```env
DJANGO_SECRET_KEY=your-very-secure-secret-key-here
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-domain.com,your-server-ip
DATABASE_URL=postgresql://scan_user:your_secure_password@localhost/scan_db
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
BINANCE_BASE_URL=https://fapi.binance.com
```

## Шаг 8: Обновление settings.py для production

Убедитесь, что в `config/settings.py` есть:

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "scan_db"),
        "USER": os.getenv("DB_USER", "scan_user"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

STATIC_ROOT = BASE_DIR / "staticfiles"
STATIC_URL = "/static/"
```

## Шаг 9: Применение миграций и сбор статики

```bash
source venv/bin/activate
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

## Шаг 10: Настройка Gunicorn

Создайте файл `gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 3
timeout = 120
keepalive = 5
```

## Шаг 11: Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/scan.service
```

Добавьте:

```ini
[Unit]
Description=Noet-Dat Gunicorn daemon
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/scan
Environment="PATH=/var/www/scan/venv/bin"
ExecStart=/var/www/scan/venv/bin/gunicorn \
    --config /var/www/scan/gunicorn_config.py \
    config.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

Запустите сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl start scan
sudo systemctl enable scan
sudo systemctl status scan
```

## Шаг 12: Настройка Nginx

```bash
sudo nano /etc/nginx/sites-available/scan
```

Добавьте конфигурацию:

```nginx
server {
    listen 80;
    server_name your-domain.com your-server-ip;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/scan/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

Активируйте конфигурацию:

```bash
sudo ln -s /etc/nginx/sites-available/scan /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Шаг 13: Настройка файрвола

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

## Шаг 14: Настройка SSL (опционально, но рекомендуется)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Шаг 15: Запуск скриптов для данных

В отдельных screen/tmux сессиях:

```bash
# Скрипт для фьючерсов
screen -S futures
cd /var/www/scan
source venv/bin/activate
python scripts/binance_ingest.py

# Скрипт для спот-монет
screen -S spot
cd /var/www/scan
source venv/bin/activate
python scripts/binance_spot_ingest.py

# Скрипт для проверки алертов (опционально, можно через cron)
screen -S alerts
cd /var/www/scan
source venv/bin/activate
TELEGRAM_BOT_TOKEN=your-token python scripts/check_alerts.py
```

Или создайте systemd сервисы для скриптов (рекомендуется).

## Шаг 16: Проверка работы

```bash
# Проверка статуса сервисов
sudo systemctl status scan
sudo systemctl status nginx

# Проверка логов
sudo journalctl -u scan -f
sudo tail -f /var/log/nginx/error.log
```

## Полезные команды

```bash
# Перезапуск приложения
sudo systemctl restart scan

# Просмотр логов
sudo journalctl -u scan -n 50

# Обновление кода
cd /var/www/scan
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
sudo systemctl restart scan
```

## Troubleshooting

1. **Ошибка подключения к БД**: Проверьте настройки в `.env` и права пользователя PostgreSQL
2. **Статика не загружается**: Убедитесь, что выполнили `collectstatic` и путь в Nginx правильный
3. **502 Bad Gateway**: Проверьте, что Gunicorn запущен (`sudo systemctl status scan`)
4. **Permission denied**: Проверьте права на файлы (`sudo chown -R ubuntu:www-data /var/www/scan`)

