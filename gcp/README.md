# utilities to load data into BigQuery

```csv2gs.sh``` shell script export data from SQLite into CSV file, then upload to Google Cloud Storage bucket. The upload will trigger function in ```cloud_function``` directory which will load data into Big Query table.

```bq``` directory contains script to load CSV to BigQuery using CLI tool.

## create cloud function by CLI

Create the service account and assign the following roles:

* BigQuery Data Owner
* BigQuery Job User
* Storage Object Admin

```shell

cd cloud_function

gcloud functions deploy load_csv_to_bigquery \
  --trigger-bucket <bucket> \
  --runtime python310 \
  --source . \
  --entry-point load_csv_to_bigquery \
  --service-account "<service-account>@<project-id>.iam.gserviceaccount.com" \
  --project <project-id> \
  --region=us-west1

# after deployment, go into console and add environment variable
# BQ_PROJECT_ID to <project-id> of the BigQuery project

gcloud functions logs read load_csv_to_bigquery  --region us-west1

```
