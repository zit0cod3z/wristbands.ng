# Gunicorn configuration for EventPro
# Designed to handle 100,000+ concurrent users with load balancing

import multiprocessing

# Bind to 4 ports – Nginx upstream will distribute across them
# Run 4 separate gunicorn processes, one per port:
# gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8001 eventpro.wsgi:application
# gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8002 eventpro.wsgi:application
# gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8003 eventpro.wsgi:application
# gunicorn -c gunicorn.conf.py --bind 0.0.0.0:8004 eventpro.wsgi:application

# Workers: (2 x CPU cores) + 1 is the recommended formula
workers = multiprocessing.cpu_count() * 2 + 1

# Use async workers for high concurrency
worker_class = 'gthread'
threads = 4

# Timeouts
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = '/var/log/gunicorn/access.log'
errorlog  = '/var/log/gunicorn/error.log'
loglevel  = 'info'

# Process naming
proc_name = 'eventpro'

# Restart workers after this many requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 100

# Preload app for faster worker spawning
preload_app = True
