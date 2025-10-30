#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
uvicorn ambassador_program.asgi:application \
    --host 0.0.0.0 \
    --port 8001 \
    --reload \
    --log-level debug
