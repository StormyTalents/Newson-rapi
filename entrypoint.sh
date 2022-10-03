#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput

# Start Celery Workers
celery worker --workdir /usr/src/app --app newson -l info &> celery.log  &

# Start Celery Beat
celery worker --workdir /usr/src/app --app newson -l info -s celerybeat-schedule.data --beat &> celery_beat.log  &

python manage.py runserver 0.0.0.0:8000
