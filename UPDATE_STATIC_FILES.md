# Инструкция по обновлению статических файлов

## Проблема
После изменения JavaScript файлов изменения не применяются на сайте.

## Решение

### 1. Пересобрать статические файлы

На сервере выполните:

```bash
cd /home/illiateslenko/project/scan  # или ваш путь к проекту
source venv/bin/activate  # активировать виртуальное окружение
python manage.py collectstatic --noinput
```

Это скопирует все файлы из `static/` в `staticfiles/`, которые обслуживает Nginx.

### 2. Проверить права доступа

```bash
# Убедитесь, что Nginx может читать файлы
sudo chown -R $USER:www-data staticfiles/
sudo chmod -R 755 staticfiles/
```

### 3. Перезапустить сервисы

```bash
# Перезапустить Django (Gunicorn)
sudo systemctl restart noetdat

# Перезапустить Nginx (опционально, если нужно)
sudo systemctl restart nginx
```

### 4. Очистить кэш браузера

В браузере:
- Нажмите `Ctrl+Shift+R` (или `Cmd+Shift+R` на Mac) для жесткой перезагрузки
- Или откройте DevTools (F12) → Network → включите "Disable cache"
- Или очистите кэш браузера полностью

### 5. Проверить, что файлы обновились

Откройте в браузере:
```
https://elcaro.online/static/js/screener.js
```

И проверьте, что в файле есть строки:
- `// Vdelta columns - use formatted values and colors from backend (same logic as OI)`
- `// Volume columns - use formatted values and colors from backend (same logic as OI)`

Если видите старую версию, значит файлы не обновились.

## Быстрая проверка

```bash
# Проверить дату изменения файла
ls -la staticfiles/js/screener.js

# Проверить содержимое файла
grep "Vdelta columns - use formatted values" staticfiles/js/screener.js
```

Если команда ничего не выводит, значит файл не обновился - нужно выполнить `collectstatic`.

## Автоматизация

Если хотите автоматизировать процесс, можно добавить в скрипт деплоя:

```bash
#!/bin/bash
cd /home/illiateslenko/project/scan
source venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart noetdat
```

