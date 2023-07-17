#!/bin/sh

if [ "$DATA_DIR" = "" ]; then
    DATA_DIR="/data/git-indexer"
fi

mkdir -p $DATA_DIR

if [ ! -d "/root/.ssh" ]; then
    # something is not right, let's wait for help
    sleep 7200
fi


if [ "$FILTER" = "" ]; then
    FILTER="*"
fi

# make sure to set SQLITE_FILE to the sqlite database file to use

PYTHONUNBUFFERED=1 python manage.py index --source gitlab --query "$QUERY" --filter "$FILTER" --upload --export-csv /tmp/all_commit_data.csv
