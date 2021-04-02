#!/usr/bin/env bash

gunicorn -c run_app.py --log-level=debug main:app --daemon
# nohup python3 main.py &
