# Инструкции по деплою на сервере

## После изменений в коде

### 1. Подключись к серверу
```bash
ssh ubuntu@your-server-ip
```

### 2. Перейди в директорию проекта
```bash
cd ~/project/noetdat
# или
cd ~/project/scan
```

### 3. Обнови код из Git
```bash
# Убедись, что нет локальных изменений
git status

# Если есть конфликты с __pycache__, удали их
git rm -r --cached accounts/__pycache__ config/__pycache__ screener/__pycache__ api/__pycache__ alerts/__pycache__ 2>/dev/null || true

# Обнови код
git pull origin main
# или
git pull origin master
```

### 4. Активируй виртуальное окружение
```bash
source venv/bin/activate
```

### 5. Установи новые зависимости (если есть)
```bash
pip install -r requirements.txt
```

### 6. Примени миграции (если есть новые)
```bash
python manage.py migrate
```

### 7. Собери статические файлы
```bash
python manage.py collectstatic --noinput
```

### 8. Скомпилируй переводы (если были изменения в локализации)
```bash
python manage.py compilemessages
```

### 9. Перезапусти Gunicorn сервис
```bash
sudo systemctl restart noetdat
```

### 10. Проверь статус сервиса
```bash
sudo systemctl status noetdat
```

### 11. Проверь логи (если есть ошибки)
```bash
sudo journalctl -u noetdat -n 50 --no-pager
```

### 12. Проверь Nginx (если нужно)
```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Быстрый деплой (все команды сразу)

```bash
cd ~/project/noetdat && \
source venv/bin/activate && \
git pull origin main && \
pip install -r requirements.txt && \
python manage.py migrate && \
python manage.py collectstatic --noinput && \
python manage.py compilemessages && \
sudo systemctl restart noetdat && \
echo "✅ Деплой завершен!"
```

## Проверка после деплоя

1. Открой сайт в браузере: `https://elcaro.online`
2. Проверь, что:
   - Язык сохраняется при обновлении данных
   - Суффиксы (K/M/B) отображаются для цен, OI и тиков
   - Темный стиль кнопки переключения языка работает
   - Все данные обновляются без задержек

## Если что-то пошло не так

### Откат изменений
```bash
cd ~/project/noetdat
git log --oneline -10  # Посмотри последние коммиты
git reset --hard HEAD~1  # Откати последний коммит
sudo systemctl restart noetdat
```

### Проверка ошибок
```bash
# Логи Gunicorn
sudo journalctl -u noetdat -n 100 --no-pager

# Логи Nginx
sudo tail -f /var/log/nginx/error.log

# Проверка Python
cd ~/project/noetdat
source venv/bin/activate
python manage.py check
```

