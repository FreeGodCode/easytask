import os
import gevent.monkey
gevent.monkey.patch_all()

import multiprocessing

debug = True
reload = True
loglevel = 'debug'
bind = "0.0.0.0:5006"
pidfile = "log/gunicorn.pid"
# accesslog = "log/access.log"
errorlog = "log/error.log"

# 启动的进程数
workers = 4
worker_class = 'gevent'
x_forwarded_for_header = 'X-FORWARDED-FOR'
