#!/bin/bash
# ROOT_PATH=`dirname $0`
# cd $ROOT_PATH
# cd ..
ps -ef|grep gun.conf|grep -v grep|awk '{print $2}'|xargs kill -9
gunicorn -c config/gun.conf wsgi_gunicorn:app --daemon