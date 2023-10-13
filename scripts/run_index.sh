#!/bin/bash


rotate_log()
{
log_file=$1
max_logs=$2

# Rotate logs
for (( i=$max_logs; i>=1; i-- )); do
    if [[ -f "${log_file}.${i}" ]]; then
        if (( i == $max_logs )); then
            rm "${log_file}.${i}" # remove the oldest log
        else
            mv "${log_file}.${i}" "${log_file}.$((i+1))"
        fi
    fi
done

if [ -f "${log_file}" ]; then
   mv ${log_file} ${log_file}.1
fi

}

RELPATH="$(dirname "$0")"/..
WORK_DIR="$(realpath $RELPATH)"
# echo WORK_DIR is $WORK_DIR

cd $WORK_DIR

rotate_log logs/cron.log 3

devbox run idx > logs/cron.log 2>&1
devbox run ipr >> logs/cron.log 2>&1

