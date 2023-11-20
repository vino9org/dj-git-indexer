# Utlity that scan git repositories and extract metrics

## Setup the environment

```shell

# easist way, use jetpack.io devbox
devbox shell

# or install python and poetry, then
poetry shell
poetry install

# or the use plain old venv
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

```

## Run

```shell
# set optional environment variables
# only set it if testing with Gitlab and GCP is desired

GITLAB_TOKEN=glpat-xxxxxx
GOOGLE_APPLICATION_CREDENTIALS=<some_crendenntial_json_file>

# index repos hosted on github, export result to CSV file then upload to Google Cloud Storage
GS_BUCKET_NAME=<gs bucket for upload> \
python manage.py index \
       --source github --query "sloppycoder/bank-demo" \
       --export-csv test.csv --upload

# index repos hosted on gitlab that matches the query and filter
python manage.py index --source gitlab --query "vino9group" --filter "test*"

# index local repos under a directory
python manage.py index --source local --query "~/tmp/repos" --db local_repos.db

# mirrors the repos hosted on gitlab to a local directory
# overwrite local directory if they already exists
python manage.py mirror --source gitlab --query "vino9group" --filter "test*" --output "~/tmp/repos" --overwrite

# run the simple gui at http://127.0.0.1:8000
python manage.py runserver
```

## Run Unit Tests

```shell
# run test and generate coverage report in HTML format in htmlcov directory
pytest -v --cov . --cov-report html

```
