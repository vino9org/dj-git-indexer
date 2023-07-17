#! /bin/bash

# export data from sqlite to csv and upload to google cloud storage

set -e

csv2gs() {
    file=$1

    if [ ! -f "$file.csv" ]; then
        echo "File $file does not exists."
        exit -1
    fi

    echo uploading $file.csv to bigquery

    gsutil cp $file.csv gs://vinolab/$file.csv

}


sqlite_to_csv()
{
sqlite3 $1 <<EOF

.headers on
.mode csv

.output all_commit_data.csv
select * from all_commit_data ;

.quit
EOF
}

sqlite_to_csv $1
csv2gs all_commit_data
