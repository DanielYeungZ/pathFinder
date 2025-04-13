#!/bin/bash

source /var/app/venv/*/bin/activate
cd /var/app/current

# Run Celery in the background and log to file
nohup celery -A celery_worker.celery worker --loglevel=info > /var/log/celery.log 2>&1 &
