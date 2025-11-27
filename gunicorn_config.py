# Gunicorn configuration file
import multiprocessing
import os

bind = "127.0.0.1:8000"

# Уменьшаем количество воркеров для стабильности
# Используем меньше воркеров, чтобы не перегружать сервер
cpu_count = multiprocessing.cpu_count()
if cpu_count <= 2:
    workers = 2
elif cpu_count <= 4:
    workers = 3
else:
    workers = 4  # Максимум 4 воркера даже на мощных серверах

worker_class = "sync"
worker_connections = 1000
timeout = 300  # Увеличено до 5 минут для медленных запросов
keepalive = 5
graceful_timeout = 120  # Время на graceful shutdown
max_requests = 1000
max_requests_jitter = 50
# Отключаем preload_app для диагностики - если есть ошибки при импорте, они будут видны сразу
# preload_app = True  # Временно отключено для диагностики
preload_app = False

# Логирование
loglevel = "info"

# Путь к логам - используем абсолютный путь или путь относительно проекта
base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(base_dir, "logs")

# Создать директорию для логов если не существует
if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

errorlog = os.path.join(log_dir, "gunicorn_error.log")
accesslog = os.path.join(log_dir, "gunicorn_access.log")

# Альтернативно, можно использовать системные логи:
# errorlog = "/var/log/gunicorn/error.log"
# accesslog = "/var/log/gunicorn/access.log"

