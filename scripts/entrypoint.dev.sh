#!/bin/bash

# exit on error
set -e

# Apply database migrations
echo "Applying database migrations"
python manage.py migrate

# Collect static files
#echo "Collecting static files"
#python manage.py collectstatic --noinput

# Start the Dev server
echo "Starting dev server"
gunicorn config.wsgi.dev:application --bind 0.0.0.0:8000 --reload &

# start celery worker
echo "Starting celery worker"
celery -A config worker -l info &

# start celery beat
echo "Starting celery beat"
celery -A config beat -l info &

# Wait for all background processes to complete
# print background jobs
jobs -l
wait
