#! /bin/bash

# import CSV file from Goolge Cloud Storage to BigQuery

set -e

csv2bq() {
    file=$1

    if [ ! -f "$file.csv" ]; then
        echo "File $file does not exists."
        exit -1
    fi

    echo uploading $file.csv to bigquery

    gsutil cp $file.csv gs://vinolab/$file.csv

   bq query --nouse_legacy_sql "delete from dev1.${file} where true"
   sleep 3
   bq load --schema=schema.json --skip_leading_rows=1 --source_format=CSV dev1."${file}" gs://vinolab/$file.csv

}

csv2bq $1
