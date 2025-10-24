"""
Gunicorn configuration for UHA API Service
"""
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2

# Logging
accesslog = "/opt/uha-api/logs/access.log"
errorlog = "/opt/uha-api/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "uha-api"

# Server mechanics
daemon = False
pidfile = "/opt/uha-api/data/gunicorn.pid"
user = "uha-api"
group = "uha-api"
umask = 0o007

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
