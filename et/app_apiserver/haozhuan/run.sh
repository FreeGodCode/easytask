#!/usr/bin/env bash

gunicorn -c run_app.py main:app --daemon

