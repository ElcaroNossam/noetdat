# Исправление ошибки "connect() failed" в Nginx

## Проблема

В логах Nginx видна ошибка:
```
connect() failed (111: Unknown error) while connecting to upstream, 
upstream: "http://127.0.0.1:8000/api/screener/..."
```

Это означает, что Nginx не может подключиться к Gunicorn на порту 8000.

## Решение

### Шаг 1: Проверьте статус Gunicorn

```bash
sudo systemctl status noetdat
```

Если сервис не запущен, запустите:
```bash
sudo systemctl start noetdat
sudo systemctl enable noetdat
```

### Шаг 2: Проверьте, на каком порту слушает Gunicorn

```bash
sudo netstat -tlnp | grep python
# или
sudo ss -tlnp | grep python
```

Должна быть строка типа:
```
tcp  0  0  127.0.0.1:8000  0.0.0.0:*  LISTEN  400/python3
```

### Шаг 3: Проверьте конфигурацию Gunicorn

```bash
cat /home/ubuntu/project/noetdat/gunicorn_config.py
```

Убедитесь, что там указан правильный порт:
```python
bind = "127.0.0.1:8000"
```

### Шаг 4: Проверьте конфигурацию Nginx

```bash
sudo cat /etc/nginx/sites-available/noetdat
```

Убедитесь, что `proxy_pass` указывает на правильный порт:
```nginx
proxy_pass http://127.0.0.1:8000;
```

### Шаг 5: Если порты не совпадают

Если Gunicorn слушает на другом порту (например, 8001), либо:

**Вариант А:** Обновите `gunicorn_config.py`:
```bash
nano /home/ubuntu/project/noetdat/gunicorn_config.py
```
Измените на:
```python
bind = "127.0.0.1:8000"
```

**Вариант Б:** Обновите Nginx конфигурацию:
```bash
sudo nano /etc/nginx/sites-available/noetdat
```
Измените `proxy_pass` на правильный порт.

### Шаг 6: Перезапустите сервисы

```bash
sudo systemctl restart noetdat
sudo systemctl restart nginx
```

### Шаг 7: Проверьте логи

```bash
# Логи Gunicorn
sudo journalctl -u noetdat -n 20

# Логи Nginx
sudo tail -20 /var/log/nginx/error.log
sudo tail -20 /var/log/nginx/access.log
```

### Шаг 8: Проверьте подключение

```bash
curl http://127.0.0.1:8000/
```

Если получаете ответ от Django, значит Gunicorn работает правильно.

## Быстрая проверка

```bash
# 1. Проверить статус
sudo systemctl status noetdat

# 2. Проверить порт
sudo ss -tlnp | grep 8000

# 3. Проверить конфигурацию
cat /home/ubuntu/project/noetdat/gunicorn_config.py | grep bind

# 4. Перезапустить
sudo systemctl restart noetdat && sudo systemctl restart nginx

# 5. Проверить логи
sudo journalctl -u noetdat -n 10
```

## Если проблема не решена

1. Проверьте, нет ли другого процесса на порту 8000:
```bash
sudo lsof -i :8000
```

2. Проверьте файрвол:
```bash
sudo ufw status
```

3. Проверьте SELinux (если используется):
```bash
getenforce
```

