#!/bin/sh

if [ "$DATABASE_URL" = "" ]; then
    echo DATABASE_URL not set, aborting.
    exit 1
fi

python manage.py migrate --check
if [ $? -ne 0 ]; then
    echo running migrations before starting app
    python manage.py migrate
fi

if [ "$RUN_MODE" != "index" ]; then
    gunicorn -w 1 crawler.wsgi --bind 0.0.0.0:8000
    exit 0
fi

if [ "$FILTER" = "" ]; then
    FILTER="*"
fi

CMD=python manage.py index --source gitlab --query "$QUERY" --filter "$FILTER"

if [ "SKIP_UPLOAD" != "1" ]; then
    CMD=$CMD --upload --export-csv /tmp/all_commit_data.csv
fi

export PYTHONUNBUFFERED=1

$CMD
