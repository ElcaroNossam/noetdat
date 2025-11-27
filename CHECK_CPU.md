# Проверка загрузки CPU на сервере

## Быстрая проверка

### 1. Проверка текущей загрузки CPU

```bash
# Показать загрузку CPU в реальном времени
top

# Или более удобный вариант
htop  # если установлен, если нет - sudo apt install htop

# Или краткая информация
uptime
```

### 2. Найти процессы, которые нагружают CPU

```bash
# Показать топ процессов по использованию CPU
ps aux --sort=-%cpu | head -20

# Или более детально
top -b -n 1 | head -20
```

### 3. Проверить конкретные скрипты

```bash
# Проверить процессы Python
ps aux | grep python

# Проверить скрипты ingest
ps aux | grep binance_ingest
ps aux | grep binance_spot_ingest
ps aux | grep telegram_bot
ps aux | grep check_alerts

# Проверить использование CPU каждым процессом
ps -eo pid,cmd,%cpu,%mem --sort=-%cpu | head -20
```

### 4. Проверить systemd сервисы

```bash
# Проверить статус всех сервисов
sudo systemctl status

# Проверить конкретные сервисы
sudo systemctl status noetdat-bot.service
sudo systemctl status noetdat-futures.service  # если есть
sudo systemctl status noetdat-spot.service      # если есть
sudo systemctl status scan.service              # Django приложение
```

### 5. Мониторинг в реальном времени

```bash
# Использование iostat (если установлен)
sudo apt install sysstat
iostat -x 1

# Или использование vmstat
vmstat 1

# Или использование mpstat
mpstat 1
```

## Возможные причины высокой загрузки CPU

1. **Скрипты ingest работают слишком часто**
   - `binance_ingest.py` обновляет каждую секунду
   - `binance_spot_ingest.py` обновляет каждую секунду
   - Это может создавать большую нагрузку

2. **Множественные экземпляры скриптов**
   - Проверьте, не запущено ли несколько копий одного скрипта

3. **Проблемы с базой данных**
   - Медленные запросы
   - Блокировки

4. **Проблемы с Django приложением**
   - Медленные запросы к API
   - Проблемы с Gunicorn

## Решения

### 1. Оптимизировать частоту обновлений

Если скрипты обновляют слишком часто, можно увеличить интервал:

В `binance_ingest.py` и `binance_spot_ingest.py` изменить:
```python
sleep_time = max(0, 1.0 - elapsed)  # Было 1 секунда
time.sleep(sleep_time)
```

На:
```python
sleep_time = max(0, 5.0 - elapsed)  # Теперь 5 секунд
time.sleep(sleep_time)
```

### 2. Остановить лишние процессы

```bash
# Найти и остановить процессы
ps aux | grep binance_ingest
kill <PID>  # или kill -9 <PID> для принудительной остановки

# Или через systemd
sudo systemctl stop noetdat-futures.service
sudo systemctl stop noetdat-spot.service
```

### 3. Проверить количество воркеров Gunicorn

В `gunicorn_config.py`:
```python
workers = multiprocessing.cpu_count() * 2 + 1  # Может быть слишком много
```

Изменить на:
```python
workers = 2  # Для небольшого сервера достаточно 2-3 воркеров
```

### 4. Оптимизировать запросы к базе данных

Проверить медленные запросы:
```bash
# В PostgreSQL
sudo -u postgres psql -d cryptoscreener
SELECT * FROM pg_stat_activity WHERE state = 'active';
```

## Команды для быстрой диагностики

```bash
# 1. Топ процессов по CPU
ps aux --sort=-%cpu | head -10

# 2. Проверить Python процессы
ps aux | grep python | awk '{print $2, $3, $11}' | sort -k2 -rn

# 3. Проверить использование памяти
free -h

# 4. Проверить использование диска
df -h

# 5. Проверить сетевую активность
sudo netstat -tulpn | grep python

# 6. Проверить логи systemd
sudo journalctl -u noetdat-bot.service -n 50
sudo journalctl -u scan.service -n 50
```

## Рекомендации

1. **Для production сервера**: Увеличьте интервал обновления до 5-10 секунд вместо 1 секунды
2. **Мониторинг**: Установите мониторинг (например, htop) для постоянного наблюдения
3. **Логирование**: Проверьте логи на наличие ошибок, которые могут вызывать бесконечные циклы

