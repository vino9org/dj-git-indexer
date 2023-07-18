#!/bin/sh

if [ "$SQLITE_FILE" = "" ]; then
    SQLITE_FILE="/data/git-indexer/git-indexer.db"
fi

if [ ! -f "$SQLITE_FILE"  ]; then
    echo $SQLITE_FILE does not exist, aborting.
    exit 1
fi

if [ "$FILTER" = "" ]; then
    FILTER="*"
fi


python manage.py migrate --check
if $? ; then
    echo running migrations before starting app
    python manage.py migrate
fi

PYTHONUNBUFFERED=1 python manage.py index --source gitlab --query "$QUERY" --filter "$FILTER" --upload --export-csv /tmp/all_commit_data.csv
