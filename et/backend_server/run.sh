#!/usr/bin/env bash

# start admin api service
# gunicorn -c config/gun.conf wsgi_gunicorn:app --daemon
gunicorn -c config/gun.conf --log-config config/gunlog.conf wsgi_gunicorn:app --daemon

# start async_task by Celery
nohup celery -A wsgi_gunicorn:celery_app worker -f ./logs/celery.log -l INFO &

# restart async_task
# celery multi restart -A wsgi_gunicorn:celery_app worker -f ./logs/celery.log -l INFO

# stop tasks --todo test
# celery multi stop -A wsgi_gunicorn:celery_app worker -f ./logs/celery.log -l INFO
