#!/bin/bash
# Скрипт для настройки автоматической очистки старых данных

echo "Настройка автоматической очистки старых snapshots..."

# Путь к проекту (измените на ваш путь)
PROJECT_DIR="/home/ubuntu/project/noetdat"
VENV_PATH="$PROJECT_DIR/venv"
MANAGE_PY="$PROJECT_DIR/manage.py"

# Проверить существование файлов
if [ ! -f "$MANAGE_PY" ]; then
    echo "ОШИБКА: $MANAGE_PY не найден!"
    echo "Измените PROJECT_DIR в этом скрипте на правильный путь к проекту."
    exit 1
fi

# Создать cron job для запуска каждые 6 часов
CRON_JOB="0 */6 * * * cd $PROJECT_DIR && $VENV_PATH/bin/python $MANAGE_PY cleanup_old_snapshots --hours 24 >> $PROJECT_DIR/logs/cleanup.log 2>&1"

# Проверить, существует ли уже такая задача
if crontab -l 2>/dev/null | grep -q "cleanup_old_snapshots"; then
    echo "Cron job для cleanup_old_snapshots уже существует."
    echo "Текущие cron jobs:"
    crontab -l | grep cleanup_old_snapshots
else
    # Добавить в crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "Cron job добавлен успешно!"
    echo ""
    echo "Задача будет запускаться каждые 6 часов и удалять snapshots старше 24 часов."
fi

echo ""
echo "Текущие cron jobs:"
crontab -l

echo ""
echo "Для проверки работы команды вручную выполните:"
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python manage.py cleanup_old_snapshots --dry-run  # Показать что будет удалено"
echo "  python manage.py cleanup_old_snapshots            # Удалить старые данные"

