# Быстрая проверка проблемы с Gunicorn

## Проблема
Воркеры Gunicorn падают через минуту после запуска, страница не грузится.

## Быстрая диагностика (выполнить на сервере)

### 1. Запустить скрипт диагностики

```bash
cd /home/ubuntu/project/noetdat  # или ваш путь
chmod +x DIAGNOSE_504.sh
./DIAGNOSE_504.sh
```

### 2. Проверить, может ли Django загрузиться

```bash
cd /home/ubuntu/project/noetdat
source venv/bin/activate
python test_django.py
```

Если есть ошибки - они будут показаны.

### 3. Проверить логи Gunicorn напрямую

```bash
# Проверить логи в директории проекта
tail -100 logs/gunicorn_error.log

# Или системные логи
sudo tail -100 /var/log/gunicorn/error.log
```

### 4. Проверить статус сервиса

```bash
sudo systemctl status noetdat.service
```

### 5. Попробовать запустить Gunicorn вручную для отладки

```bash
cd /home/ubuntu/project/noetdat
source venv/bin/activate

# Запустить Gunicorn вручную (будет видно ошибки в консоли)
gunicorn --bind 127.0.0.1:8000 --workers 1 --timeout 120 config.wsgi:application
```

Если есть ошибки - они будут видны в консоли.

### 6. Проверить подключение к базе данных

```bash
# Проверить PostgreSQL
sudo systemctl status postgresql

# Попробовать подключиться
sudo -u postgres psql -d cryptoscreener -c "SELECT 1;"
```

### 7. Проверить переменные окружения

```bash
cd /home/ubuntu/project/noetdat
cat .env | grep -v PASSWORD  # Показать все кроме паролей
```

## Возможные причины и решения

### Причина 1: Ошибка при импорте Django

**Симптомы:** В логах видны `ImportError` или `ModuleNotFoundError`

**Решение:**
```bash
source venv/bin/activate
pip install -r requirements.txt
python manage.py check
```

### Причина 2: Проблемы с базой данных

**Симптомы:** Ошибки подключения к БД в логах

**Решение:**
```bash
# Проверить настройки БД в .env
cat .env | grep DB_

# Проверить PostgreSQL
sudo systemctl restart postgresql
sudo systemctl status postgresql
```

### Причина 3: Ошибки в коде Django

**Симптомы:** Ошибки при загрузке моделей или views

**Решение:**
```bash
python manage.py check
python manage.py migrate
```

### Причина 4: Проблемы с путями

**Симптомы:** `FileNotFoundError` или неправильные пути

**Решение:**
```bash
# Проверить, что все пути правильные в systemd service
sudo cat /etc/systemd/system/noetdat.service

# Убедиться, что WorkingDirectory правильный
```

## Временное решение

Если нужно быстро восстановить работу:

```bash
# 1. Остановить сервис
sudo systemctl stop noetdat.service

# 2. Отредактировать gunicorn_config.py - отключить preload_app
# (уже сделано в коде)

# 3. Перезапустить
sudo systemctl daemon-reload
sudo systemctl start noetdat.service

# 4. Смотреть логи в реальном времени
sudo journalctl -u noetdat.service -f
```

## После исправления

```bash
# Включить preload_app обратно для производительности
# (в gunicorn_config.py изменить preload_app = False на preload_app = True)

sudo systemctl restart noetdat.service
```

