import os
import gevent.monkey
import multiprocessing
gevent.monkey.patch_all()  # 猴子补丁

debug = True
loglevel = 'error'
bind = "0.0.0.0:5007"
pidfile = "log/gunicorn.pid"
# accesslog = "log/access.log"
errorlog = "log/debug.log"

# 启动的进程数
workers = multiprocessing.cpu_count()
worker_class = 'gevent'
x_forwarded_for_header = 'X-FORWARDED-FOR'
reload = True
