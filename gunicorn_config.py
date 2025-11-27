import multiprocessing
import os

bind = "127.0.0.1:8000"

cpu_count = multiprocessing.cpu_count()
if cpu_count <= 2:
    workers = 2
elif cpu_count <= 4:
    workers = 3
else:
    workers = 4

worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
graceful_timeout = 60
max_requests = 1000
max_requests_jitter = 50
preload_app = True

loglevel = "info"

base_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(base_dir, "logs")

if not os.path.exists(log_dir):
    os.makedirs(log_dir, exist_ok=True)

errorlog = os.path.join(log_dir, "gunicorn_error.log")
accesslog = os.path.join(log_dir, "gunicorn_access.log")

