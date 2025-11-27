# Автоматическая очистка старых данных

## Описание

Management command `cleanup_old_snapshots` автоматически удаляет старые записи из таблицы `ScreenerSnapshot`, чтобы поддерживать размер базы данных на разумном уровне.

По умолчанию удаляются все snapshots старше 24 часов.

## Использование

### Ручной запуск

```bash
cd /home/ubuntu/project/noetdat  # или ваш путь к проекту
source venv/bin/activate

# Показать что будет удалено (без фактического удаления)
python manage.py cleanup_old_snapshots --dry-run

# Удалить snapshots старше 24 часов (по умолчанию)
python manage.py cleanup_old_snapshots

# Удалить snapshots старше 48 часов
python manage.py cleanup_old_snapshots --hours 48

# Удалить snapshots старше 12 часов
python manage.py cleanup_old_snapshots --hours 12
```

### Параметры

- `--hours N` - Удалить snapshots старше N часов (по умолчанию: 24)
- `--dry-run` - Показать что будет удалено без фактического удаления

## Настройка автоматической очистки

### Вариант 1: Использовать готовый скрипт

```bash
# 1. Отредактировать путь к проекту в скрипте (если нужно)
nano setup_cleanup_cron.sh

# 2. Запустить скрипт
chmod +x setup_cleanup_cron.sh
./setup_cleanup_cron.sh
```

### Вариант 2: Настроить вручную через crontab

```bash
# 1. Открыть crontab для редактирования
crontab -e

# 2. Добавить строку (замените путь на ваш):
0 */6 * * * cd /home/ubuntu/project/noetdat && /home/ubuntu/project/noetdat/venv/bin/python /home/ubuntu/project/noetdat/manage.py cleanup_old_snapshots --hours 24 >> /home/ubuntu/project/noetdat/logs/cleanup.log 2>&1

# 3. Сохранить и выйти
```

### Вариант 3: Использовать systemd timer (более надежно)

Создать файл `/etc/systemd/system/noetdat-cleanup.service`:

```ini
[Unit]
Description=Noet-Dat cleanup old snapshots
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/project/noetdat
Environment="PATH=/home/ubuntu/project/noetdat/venv/bin"
ExecStart=/home/ubuntu/project/noetdat/venv/bin/python /home/ubuntu/project/noetdat/manage.py cleanup_old_snapshots --hours 24
StandardOutput=append:/home/ubuntu/project/noetdat/logs/cleanup.log
StandardError=append:/home/ubuntu/project/noetdat/logs/cleanup.log
```

Создать файл `/etc/systemd/system/noetdat-cleanup.timer`:

```ini
[Unit]
Description=Run Noet-Dat cleanup every 6 hours
Requires=noetdat-cleanup.service

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Запустить:

```bash
sudo systemctl daemon-reload
sudo systemctl enable noetdat-cleanup.timer
sudo systemctl start noetdat-cleanup.timer
sudo systemctl status noetdat-cleanup.timer
```

## Проверка работы

### Проверить cron job

```bash
# Показать все cron jobs
crontab -l

# Проверить логи cron (если настроены)
grep CRON /var/log/syslog | tail -20
```

### Проверить systemd timer

```bash
# Статус timer
sudo systemctl status noetdat-cleanup.timer

# Список всех timers
systemctl list-timers

# Логи service
sudo journalctl -u noetdat-cleanup.service -n 50
```

### Проверить логи очистки

```bash
# Если логи пишутся в файл
tail -50 /home/ubuntu/project/noetdat/logs/cleanup.log
```

## Мониторинг размера базы данных

```bash
# Размер таблицы ScreenerSnapshot
sudo -u postgres psql -d cryptoscreener -c "
SELECT 
    pg_size_pretty(pg_total_relation_size('screener_screenersnapshot')) AS total_size,
    pg_size_pretty(pg_relation_size('screener_screenersnapshot')) AS table_size,
    COUNT(*) AS row_count
FROM screener_screenersnapshot;
"

# Количество записей по часам
sudo -u postgres psql -d cryptoscreener -c "
SELECT 
    DATE_TRUNC('hour', ts) AS hour,
    COUNT(*) AS count
FROM screener_screenersnapshot
WHERE ts >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour DESC;
"
```

## Рекомендации

1. **Частота очистки**: Рекомендуется запускать каждые 6 часов
2. **Период хранения**: 24 часа достаточно для работы скринера
3. **Мониторинг**: Регулярно проверяйте размер базы данных и логи очистки
4. **Резервное копирование**: Если нужны исторические данные, настройте бэкапы перед очисткой

## Устранение проблем

### Команда не найдена

```bash
# Убедитесь, что вы в правильной директории
cd /home/ubuntu/project/noetdat

# Убедитесь, что виртуальное окружение активировано
source venv/bin/activate

# Проверьте, что команда доступна
python manage.py help cleanup_old_snapshots
```

### Ошибки прав доступа

```bash
# Убедитесь, что у пользователя есть права на запись в БД
# Проверьте настройки в .env файле
```

### Cron не запускается

```bash
# Проверьте путь к Python в cron job
which python  # В обычной сессии
# В cron job должен быть полный путь к Python из venv

# Проверьте логи cron
grep CRON /var/log/syslog | grep cleanup
```

