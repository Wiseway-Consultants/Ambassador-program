#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn ambassador_program.asgi:application -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8001 --timeout 0 --access-logfile - --error-logfile -
