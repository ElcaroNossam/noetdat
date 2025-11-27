#!/bin/bash
# Скрипт для диагностики проблемы с Gunicorn

echo "=== Диагностика проблемы с Gunicorn ==="
echo ""

echo "1. Статус сервиса:"
sudo systemctl status noetdat.service --no-pager -l | head -20
echo ""

echo "2. Проверка процессов Gunicorn:"
ps aux | grep gunicorn | grep -v grep
echo ""

echo "3. Последние логи systemd (50 строк):"
sudo journalctl -u noetdat.service -n 50 --no-pager | tail -30
echo ""

echo "4. Проверка логов Gunicorn (если есть):"
if [ -f "logs/gunicorn_error.log" ]; then
    echo "--- Последние 30 строк logs/gunicorn_error.log ---"
    tail -30 logs/gunicorn_error.log
else
    echo "Файл logs/gunicorn_error.log не найден"
fi
echo ""

echo "5. Проверка системных логов Gunicorn (если есть):"
if [ -f "/var/log/gunicorn/error.log" ]; then
    echo "--- Последние 30 строк /var/log/gunicorn/error.log ---"
    sudo tail -30 /var/log/gunicorn/error.log
else
    echo "Файл /var/log/gunicorn/error.log не найден"
fi
echo ""

echo "6. Проверка доступности порта 8000:"
sudo netstat -tulpn | grep 8000 || sudo ss -tulpn | grep 8000
echo ""

echo "7. Проверка подключения к Gunicorn:"
curl -I http://127.0.0.1:8000/ 2>&1 | head -10
echo ""

echo "8. Проверка использования ресурсов:"
echo "--- CPU и память ---"
top -bn1 | head -5
echo ""
free -h
echo ""

echo "9. Проверка процессов Python:"
ps aux | grep python | grep -v grep | head -10
echo ""

echo "10. Проверка базы данных:"
sudo systemctl status postgresql --no-pager | head -5
echo ""

echo "11. Проверка Django (если возможно):"
if [ -f "manage.py" ]; then
    source venv/bin/activate 2>/dev/null
    python manage.py check 2>&1 | head -20
    deactivate 2>/dev/null
else
    echo "manage.py не найден в текущей директории"
fi
echo ""

echo "=== Конец диагностики ==="

