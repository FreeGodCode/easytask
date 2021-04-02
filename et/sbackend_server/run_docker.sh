#!/bin/sh

nohup nginx &

cd /
cd /back_server

# start admin api service
gunicorn -c config/gun.conf wsgi_gunicorn:app --daemon

# start async_task by Celery
celery -A wsgi_gunicorn:celery_app worker -f ./logs/celery.log -l INFO

