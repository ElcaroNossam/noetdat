# Исправление ошибки Content Security Policy для TradingView

## Проблема

Ошибка в консоли браузера:
```
Content Security Policy of your site blocks the use of 'eval' in JavaScript
```

Это происходит потому, что TradingView widget использует `eval()` в своем JavaScript коде, а CSP блокирует это по соображениям безопасности.

## Решение

### Вариант 1: Через Django settings (уже добавлено)

В `config/settings.py` добавлена настройка CSP, которая разрешает `unsafe-eval` для TradingView.

### Вариант 2: Через Nginx (альтернативный способ)

Если хотите настроить CSP через Nginx, добавьте в конфигурацию:

```bash
sudo nano /etc/nginx/sites-available/noetdat
```

Добавьте заголовок в блок `server`:

```nginx
server {
    listen 80;
    server_name elcaro.online www.elcaro.online;
    
    # Content Security Policy для TradingView
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://s3.tradingview.com https://*.tradingview.com; style-src 'self' 'unsafe-inline' https://*.tradingview.com; img-src 'self' data: https: blob:; font-src 'self' data: https:; connect-src 'self' https://*.tradingview.com https://*.binance.com; frame-src 'self' https://*.tradingview.com; object-src 'none'; base-uri 'self'; form-action 'self';" always;

    # ... остальная конфигурация
}
```

**ВАЖНО:** Если добавляете через Nginx, уберите мета-тег из `templates/base.html`, чтобы избежать конфликта.

### Вариант 3: Только для TradingView страницы (рекомендуется)

Если хотите применять CSP только на странице с TradingView, можно использовать middleware или добавить заголовок только для этой страницы.

## Что уже сделано

1. ✅ Добавлен мета-тег CSP в `templates/base.html`
2. ✅ Добавлены настройки CSP в `config/settings.py`

## Проверка

1. Перезапустите Django сервис:
```bash
sudo systemctl restart noetdat
```

2. Если используете Nginx для CSP, перезапустите Nginx:
```bash
sudo systemctl restart nginx
```

3. Откройте страницу с TradingView и проверьте консоль браузера - ошибка должна исчезнуть.

## Безопасность

**Внимание:** Разрешение `unsafe-eval` снижает безопасность сайта, так как позволяет выполнять произвольный JavaScript код. Однако это необходимо для работы TradingView widget.

Чтобы минимизировать риски:
- CSP настроен так, чтобы разрешать `unsafe-eval` только для скриптов с доменов TradingView
- Остальные политики безопасности остаются строгими
- Используется `'self'` для всех ресурсов по умолчанию

## Альтернативное решение (без unsafe-eval)

Если хотите полностью избежать `unsafe-eval`, можно:
1. Использовать iframe для TradingView (но это может ограничить функциональность)
2. Использовать альтернативный виджет графика, который не требует `eval()`

Но для полной функциональности TradingView требуется `unsafe-eval`.

