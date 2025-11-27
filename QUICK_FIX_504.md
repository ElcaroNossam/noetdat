# Быстрое исправление 504 ошибки

## Проблема
Gunicorn воркеры падают, сайт не отображается (504 Gateway Time-out).

## Решение (выполнить на сервере)

### 1. Остановить сервисы

```bash
sudo systemctl stop noetdat.service
sudo systemctl stop noetdat-bot.service
# Остановить скрипты ingest если они запущены
sudo systemctl stop noetdat-futures.service 2>/dev/null || true
sudo systemctl stop noetdat-spot.service 2>/dev/null || true
```

### 2. Обновить код на сервере

```bash
cd /home/ubuntu/project/noetdat  # или ваш путь
git pull  # если используете git
# Или скопировать обновленный gunicorn_config.py
```

### 3. Создать директорию для логов

```bash
cd /home/ubuntu/project/noetdat
mkdir -p logs
chmod 755 logs
```

### 4. Проверить Django

```bash
source venv/bin/activate
python manage.py check
python manage.py migrate  # если есть новые миграции
```

### 5. Перезапустить Gunicorn

```bash
sudo systemctl daemon-reload
sudo systemctl start noetdat.service
sudo systemctl status noetdat.service
```

### 6. Проверить работу

```bash
# Проверить воркеры
ps aux | grep gunicorn

# Проверить доступность
curl -I http://127.0.0.1:8000/

# Посмотреть логи
sudo journalctl -u noetdat.service -n 50
tail -50 logs/gunicorn_error.log
```

## Если проблема сохраняется

### Проверить логи на ошибки

```bash
# Логи systemd
sudo journalctl -u noetdat.service -n 100 --no-pager

# Логи Gunicorn
tail -100 logs/gunicorn_error.log

# Логи Nginx
sudo tail -100 /var/log/nginx/error.log
```

### Временно уменьшить нагрузку

```bash
# Остановить скрипты ingest
sudo systemctl stop noetdat-futures.service 2>/dev/null || true
sudo systemctl stop noetdat-spot.service 2>/dev/null || true

# Проверить использование ресурсов
top
free -h
```

### Проверить конфигурацию systemd

```bash
# Проверить путь к конфигурации Gunicorn
sudo cat /etc/systemd/system/noetdat.service | grep gunicorn_config

# Убедиться, что путь правильный
# Должно быть что-то вроде:
# --config /home/ubuntu/project/noetdat/gunicorn_config.py
```

## Основные изменения

1. **Уменьшено количество воркеров** - с `cpu_count * 2 + 1` до максимум 4 воркеров
2. **Добавлено логирование** - логи теперь в `logs/gunicorn_error.log`
3. **Оптимизирована конфигурация** - для стабильной работы на небольших серверах

## После исправления

```bash
# Запустить скрипты ingest обратно (если нужно)
sudo systemctl start noetdat-futures.service
sudo systemctl start noetdat-spot.service

# Проверить статус всех сервисов
sudo systemctl status noetdat.service
sudo systemctl status noetdat-bot.service
```

