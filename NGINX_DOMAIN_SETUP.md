# Настройка Nginx для домена elcaro.online

## Шаг 1: Обновление конфигурации Nginx

Отредактируйте файл конфигурации Nginx:

```bash
sudo nano /etc/nginx/sites-available/noetdat
```

**Примечание:** На вашем сервере конфигурация называется `noetdat`, а не `scan`.

## Шаг 2: Обновите server_name

В конфигурации Nginx найдите строку `server_name` и обновите её:

```nginx
server {
    listen 80;
    server_name elcaro.online www.elcaro.online;

    client_max_body_size 10M;

    location /static/ {
        alias /home/ubuntu/project/noetdat/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

**ВАЖНО:** Замените путь `/var/www/scan/staticfiles/` на реальный путь к вашему проекту, если он отличается.

## Шаг 3: Проверьте конфигурацию

```bash
sudo nginx -t
```

Если всё ОК, вы увидите:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

## Шаг 4: Перезапустите Nginx

```bash
sudo systemctl restart nginx
```

## Шаг 5: Обновите переменную окружения ALLOWED_HOSTS

Отредактируйте файл `.env` в корне проекта:

```bash
nano .env
```

Добавьте или обновите строку:

```env
ALLOWED_HOSTS=elcaro.online,www.elcaro.online,localhost,127.0.0.1
```

Или если хотите оставить IP сервера:

```env
ALLOWED_HOSTS=elcaro.online,www.elcaro.online,localhost,127.0.0.1,18.196.22.113
```

## Шаг 6: Перезапустите Django сервис

```bash
sudo systemctl restart noetdat
sudo systemctl status noetdat
```

**ВАЖНО:** Если видите ошибки "connect() failed" в логах Nginx, проверьте:

1. На каком порту слушает Gunicorn:
```bash
sudo netstat -tlnp | grep gunicorn
# или
sudo ss -tlnp | grep gunicorn
```

2. Проверьте конфигурацию Gunicorn:
```bash
cat /home/ubuntu/project/noetdat/gunicorn_config.py
```

3. Убедитесь, что порт в Nginx совпадает с портом в Gunicorn (обычно 8000)

## Шаг 7: Настройка DNS

Убедитесь, что DNS записи для домена настроены правильно:

1. **A запись** для `elcaro.online` → IP вашего сервера (18.196.22.113)
2. **A запись** для `www.elcaro.online` → IP вашего сервера (18.196.22.113)

Или используйте CNAME для www:
- **A запись** для `elcaro.online` → 18.196.22.113
- **CNAME запись** для `www.elcaro.online` → `elcaro.online`

## Шаг 8: Настройка SSL (рекомендуется)

После настройки DNS и проверки работы сайта, установите SSL сертификат:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d elcaro.online -d www.elcaro.online
```

Certbot автоматически обновит конфигурацию Nginx для HTTPS.

## Проверка

1. Проверьте, что сайт открывается:
   ```bash
   curl -I http://elcaro.online
   ```

2. Проверьте логи Nginx:
   ```bash
   sudo tail -f /var/log/nginx/access.log
   sudo tail -f /var/log/nginx/error.log
   ```

3. Проверьте логи Django:
   ```bash
   sudo journalctl -u noetdat -f
   ```

## Быстрая команда для всего процесса

```bash
# 1. Обновить .env
echo "ALLOWED_HOSTS=elcaro.online,www.elcaro.online,localhost,127.0.0.1" >> .env

# 2. Обновить Nginx (вручную отредактируйте /etc/nginx/sites-available/scan)

# 3. Проверить и перезапустить
sudo nginx -t && sudo systemctl restart nginx
sudo systemctl restart scan
```

## Если что-то не работает

1. Проверьте DNS:
   ```bash
   nslookup elcaro.online
   nslookup www.elcaro.online
   ```

2. Проверьте, что порт 80 открыт:
   ```bash
   sudo ufw status
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

3. Проверьте логи:
   ```bash
   sudo tail -50 /var/log/nginx/error.log
   sudo journalctl -u noetdat -n 50
   ```

## Решение ошибки "connect() failed (111)"

Если в логах Nginx видите ошибку "connect() failed (111: Unknown error) while connecting to upstream", это означает, что Gunicorn не слушает на порту 8000 или не запущен.

**Решение:**

1. Проверьте, запущен ли Gunicorn:
```bash
sudo systemctl status noetdat
```

2. Проверьте, на каком порту он слушает:
```bash
sudo netstat -tlnp | grep python
# или
sudo ss -tlnp | grep python
```

3. Проверьте конфигурацию Gunicorn:
```bash
cat /home/ubuntu/project/noetdat/gunicorn_config.py
```

Убедитесь, что там указан правильный порт (обычно `bind = "127.0.0.1:8000"`).

4. Если порт другой, либо:
   - Обновите `gunicorn_config.py` чтобы использовать порт 8000
   - Или обновите Nginx конфигурацию чтобы использовать правильный порт

5. Перезапустите сервис:
```bash
sudo systemctl restart noetdat
sudo systemctl restart nginx
```

6. Проверьте логи:
```bash
sudo journalctl -u noetdat -n 20
sudo tail -20 /var/log/nginx/error.log
```

