#!/bin/bash
# Быстрое обновление статических файлов

cd /home/illiateslenko/project/scan

echo "1. Активация виртуального окружения..."
source venv/bin/activate

echo "2. Пересборка статических файлов..."
python manage.py collectstatic --noinput

echo "3. Проверка прав доступа..."
sudo chown -R $USER:www-data staticfiles/ 2>/dev/null || chown -R $USER:www-data staticfiles/
sudo chmod -R 755 staticfiles/ 2>/dev/null || chmod -R 755 staticfiles/

echo "4. Перезапуск Django сервиса..."
sudo systemctl restart noetdat

echo "5. Проверка обновления..."
if grep -q "Vdelta columns - use formatted values" staticfiles/js/screener.js; then
    echo "✅ Файл обновлен успешно!"
else
    echo "❌ Файл не обновлен, проверьте ошибки выше"
fi

echo ""
echo "Готово! Теперь:"
echo "1. Очистите кэш браузера (Ctrl+Shift+R)"
echo "2. Проверьте сайт"

