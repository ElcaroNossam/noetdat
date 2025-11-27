# Исправление проблемы с отображением стилей на сервере

## Причины проблемы

1. Не выполнен `collectstatic` - статические файлы не собраны в `staticfiles/`
2. Неправильный путь в Nginx - не совпадает с `STATIC_ROOT`
3. Неправильные права доступа к файлам
4. Nginx не может найти файлы по указанному пути

## Решение

### Шаг 1: Проверьте настройки в settings.py

Убедитесь, что в `config/settings.py` есть:

```python
STATIC_URL = "static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"
```

### Шаг 2: Соберите статические файлы

На сервере выполните:

```bash
cd /var/www/scan  # или /home/ubuntu/project/noetdat - ваш путь
source venv/bin/activate
python manage.py collectstatic --noinput
```

Это создаст директорию `staticfiles/` со всеми статическими файлами.

### Шаг 3: Проверьте права доступа

```bash
# Убедитесь, что Nginx может читать файлы
sudo chown -R ubuntu:www-data /var/www/scan/staticfiles
sudo chmod -R 755 /var/www/scan/staticfiles
```

### Шаг 4: Проверьте конфигурацию Nginx

Убедитесь, что в `/etc/nginx/sites-available/scan` путь правильный:

```nginx
location /static/ {
    alias /var/www/scan/staticfiles/;  # Путь должен совпадать с STATIC_ROOT
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

**ВАЖНО:** Путь должен быть абсолютным и заканчиваться на `/`

### Шаг 5: Проверьте путь в settings.py

Если ваш проект находится в `/home/ubuntu/project/noetdat`, то:

```python
STATIC_ROOT = BASE_DIR / "staticfiles"  # Это будет /home/ubuntu/project/noetdat/staticfiles
```

И в Nginx должно быть:

```nginx
location /static/ {
    alias /home/ubuntu/project/noetdat/staticfiles/;
    ...
}
```

### Шаг 6: Перезапустите сервисы

```bash
# Проверьте конфигурацию Nginx
sudo nginx -t

# Если все ОК, перезапустите
sudo systemctl restart nginx
sudo systemctl restart scan  # ваш Django сервис
```

### Шаг 7: Проверьте логи

```bash
# Логи Nginx
sudo tail -f /var/log/nginx/error.log

# Логи Django
sudo journalctl -u scan -f
```

## Быстрая проверка

1. Проверьте, что файлы существуют:
   ```bash
   ls -la /var/www/scan/staticfiles/css/style.css
   ```

2. Проверьте права:
   ```bash
   ls -la /var/www/scan/staticfiles/
   ```

3. Проверьте в браузере:
   - Откройте: `http://your-server-ip/static/css/style.css`
   - Должен отображаться CSS файл, а не 404

## Типичные ошибки

1. **404 Not Found** - неправильный путь в Nginx или файлы не собраны
2. **403 Forbidden** - неправильные права доступа
3. **Пустая страница** - файлы не собраны (выполните `collectstatic`)

## Автоматическое исправление

Выполните на сервере:

```bash
cd /var/www/scan  # или ваш путь к проекту
source venv/bin/activate
python manage.py collectstatic --noinput
sudo chown -R ubuntu:www-data staticfiles/
sudo chmod -R 755 staticfiles/
sudo systemctl restart nginx
```

