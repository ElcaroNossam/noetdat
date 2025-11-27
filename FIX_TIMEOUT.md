# Исправление проблемы с таймаутами воркеров

## Проблема
Воркеры Gunicorn падают из-за таймаута (WORKER TIMEOUT) - запросы к базе данных выполняются слишком долго.

## Что было исправлено

### 1. Увеличен timeout в Gunicorn
- Было: `timeout = 120` (2 минуты)
- Стало: `timeout = 300` (5 минут)
- Добавлен: `graceful_timeout = 120`

### 2. Оптимизированы запросы к базе данных

**Было:** Использовался Window function с RowNumber(), который очень медленный на больших таблицах:
```python
qs = ScreenerSnapshot.objects.annotate(
    row_number=Window(
        expression=RowNumber(),
        partition_by=[F("symbol")],
        order_by=[F("ts").desc()],
    )
).filter(row_number=1)
```

**Стало:** Используется более эффективный подзапрос:
```python
latest_ts_per_symbol = ScreenerSnapshot.objects.filter(
    symbol=OuterRef("symbol")
).values("symbol").annotate(max_ts=Max("ts")).values("max_ts")[:1]

qs = ScreenerSnapshot.objects.filter(
    ts=Subquery(latest_ts_per_symbol)
).select_related("symbol").distinct("symbol")
```

Этот подход:
- Использует индекс на `(symbol, -ts)`
- Не требует сортировки всех записей
- Работает намного быстрее на больших таблицах

## Что нужно сделать на сервере

### 1. Обновить код

```bash
cd /home/ubuntu/project/noetdat
git pull  # или скопировать обновленные файлы
```

### 2. Перезапустить Gunicorn

```bash
sudo systemctl daemon-reload
sudo systemctl restart noetdat.service
sudo systemctl status noetdat.service
```

### 3. Проверить работу

```bash
# Проверить логи
tail -50 logs/gunicorn_error.log

# Проверить доступность
curl -I http://127.0.0.1:8000/

# Смотреть логи в реальном времени
sudo journalctl -u noetdat.service -f
```

## Дополнительные оптимизации (если проблема сохраняется)

### 1. Очистить старые данные

Если в таблице ScreenerSnapshot слишком много старых записей, можно их удалить:

```bash
source venv/bin/activate
python manage.py shell
```

```python
from screener.models import ScreenerSnapshot
from django.utils import timezone
from datetime import timedelta

# Удалить записи старше 7 дней
cutoff = timezone.now() - timedelta(days=7)
count = ScreenerSnapshot.objects.filter(ts__lt=cutoff).delete()[0]
print(f"Deleted {count} old snapshots")
```

### 2. Добавить ограничение на количество записей в запросе

Можно ограничить запрос только последними N часами:

```python
from django.utils import timezone
from datetime import timedelta

# Только последние 24 часа
recent_cutoff = timezone.now() - timedelta(hours=24)
qs = qs.filter(ts__gte=recent_cutoff)
```

### 3. Проверить индексы в базе данных

```bash
sudo -u postgres psql -d cryptoscreener
```

```sql
-- Проверить индексы
\d screener_screenersnapshot

-- Если индекса нет, создать:
CREATE INDEX IF NOT EXISTS screener_screenersnapshot_symbol_ts_idx 
ON screener_screenersnapshot(symbol_id, ts DESC);
```

## Мониторинг

После исправления следите за:
- Логами Gunicorn на наличие таймаутов
- Временем выполнения запросов
- Использованием памяти и CPU

```bash
# Проверить использование ресурсов
top
free -h

# Проверить медленные запросы в PostgreSQL
sudo -u postgres psql -d cryptoscreener -c "
SELECT pid, now() - pg_stat_activity.query_start AS duration, query 
FROM pg_stat_activity 
WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';
"
```

