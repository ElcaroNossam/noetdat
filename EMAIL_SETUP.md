# Настройка Email сервера

Для работы системы регистрации и подтверждения email необходимо настроить SMTP сервер.

## Переменные окружения (.env)

Добавьте следующие переменные в ваш `.env` файл:

```bash
# Email настройки
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

## Примеры настройки для разных провайдеров

### Gmail

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Используйте App Password, не обычный пароль
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Важно для Gmail:**
1. Включите двухфакторную аутентификацию
2. Создайте App Password: https://myaccount.google.com/apppasswords
3. Используйте App Password вместо обычного пароля

### Yandex Mail

```bash
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@yandex.ru
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@yandex.ru
```

### Mail.ru

```bash
EMAIL_HOST=smtp.mail.ru
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=your-email@mail.ru
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=your-email@mail.ru
```

### SendGrid

```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## Тестирование настройки

После настройки переменных окружения, перезапустите сервер и попробуйте зарегистрироваться.

Если email не отправляется, проверьте:
1. Правильность настроек в `.env`
2. Логи Django (проверьте настройки `EMAIL_BACKEND`)
3. Брандмауэр сервера (порты 587, 465 должны быть открыты)

## Отладка

Для отладки можно временно использовать консольный backend:

```python
# В settings.py
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

Это будет выводить письма в консоль вместо отправки.

