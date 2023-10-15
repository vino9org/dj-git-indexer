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

run_index()
{
    mode=$1

    if [ "$mode" = "commit" ]; then
        echo "Login to Gitlab"
        pushd ../gitlab_login_bot
        poetry run python -u gitlab_login.py
        popd

        echo "Indexing commits"
        $BASE_COMMAND  --export-csv db/all_commit_data.csv

    elif [ "$mode" = "mr" ]; then
        echo "Indexing merge requests"
        $BASE_COMMAND  --merge_requests_only

    else
        echo unknown mode $mode
    fi
}

BASE_COMMAND="poetry run python -u manage.py index --source gitlab --query 'securitybankph/' --filter '*' "
RELPATH="$(dirname "$0")"/..
WORK_DIR="$(realpath $RELPATH)"
# echo WORK_DIR is $WORK_DIR

cd $WORK_DIR

rotate_log logs/cron.log 3


case $2 in
    idx)
        run_index commit
        ;;
    ipr)
        run_index mr
        ;;
    *)
        run_index commit
        run_index mr
        ;;
esac
