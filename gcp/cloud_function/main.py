import os

from google.cloud.bigquery import Client, LoadJobConfig, SchemaField, SourceFormat

# Configure your project and BigQuery dataset
project_id = os.environ.get("BQ_PROJECT_ID")
dataset_id = "dev1"
table_id = "all_commit_data"

# Instantiate the BigQuery client
client = Client(project=project_id)


def load_csv_to_bigquery(data, context):
    # Get the file details from the event
    bucket_name = data["bucket"]
    file_name = data["name"]
    file_path = f"gs://{bucket_name}/{file_name}"

    # Skip processing if the file is not named "all_commit_data.csv"
    if file_name != "all_commit_data.csv":
        return

    # Delete all rows in the existing BigQuery table
    delete_query = f"DELETE FROM `{project_id}.{dataset_id}.{table_id}` WHERE true"
    client.query(delete_query).result()

    # Load the CSV file into BigQuery
    job_config = LoadJobConfig(
        schema=[
            SchemaField(name="author_id", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="name", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="email", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="real_name", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="real_email", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="company", field_type="STRING", mode="NULLABLE"),
            SchemaField(name="team", field_type="STRING", mode="NULLABLE"),
            SchemaField(name="author_group", field_type="STRING", mode="NULLABLE"),
            SchemaField(name="sha", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="commit_date", field_type="TIMESTAMP", mode="REQUIRED"),
            SchemaField(name="commit_date_ts", field_type="TIMESTAMP", mode="REQUIRED"),
            SchemaField(name="is_merge", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="commit_n_lines", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="commit_n_files", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="commit_n_insertions", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="commit_n_deletions", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="commit_n_lines_changed", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="commit_n_lines_ignored", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="commit_n_files_changed", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="commit_n_files_ignored", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="committed_file_id", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="change_type", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="file_path", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="file_name", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="file_type", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="n_lines_added", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="n_lines_deleted", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="n_lines_changed", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="n_lines_of_code", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="n_methods", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="n_methods_changed", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="is_on_exclude_list", field_type="BOOLEAN", mode="REQUIRED"),
            SchemaField(name="is_superfluous", field_type="BOOLEAN", mode="REQUIRED"),
            SchemaField(name="repo_name", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="repo_group", field_type="STRING", mode="NULLABLE"),
            SchemaField(name="repo_type", field_type="STRING", mode="NULLABLE"),
            SchemaField(name="component", field_type="STRING", mode="NULLABLE"),
            SchemaField(name="clone_url", field_type="STRING", mode="REQUIRED"),
            SchemaField(name="browse_url", field_type="STRING", mode="NULLABLE"),
            SchemaField(name="repo_id", field_type="INTEGER", mode="REQUIRED"),
            SchemaField(name="repo_inlude_in_stats", field_type="BOOLEAN", mode="REQUIRED"),
            SchemaField(name="last_indexed_at", field_type="TIMESTAMP", mode="NULLABLE"),
        ],
        skip_leading_rows=1,  # Skip the header row
        source_format=SourceFormat.CSV,
    )

    table_ref = client.dataset(dataset_id).table(table_id)

    # Load the data into BigQuery
    try:
        load_job = client.load_table_from_uri(file_path, table_ref, job_config=job_config)
        load_job.result()  # Waits for the job to complete

        print(f"CSV file {file_path} loaded into BigQuery table {table_id}")
    except Exception as e:
        print(f"Error loading CSV file {file_path}: {str(e)}")

    # # Optionally, delete the file from Cloud Storage after loading it into BigQuery
    # try:
    #     os.remove(file_name)
    # except Exception as e:
    #     print(f"Error deleting CSV file {file_path}: {str(e)}")
