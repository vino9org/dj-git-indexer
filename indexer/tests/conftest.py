import os
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime, timezone

import pytest
from django.conf import settings
from django.core.management import call_command
from github import Auth, Github
from gitlab import Gitlab

from indexer.models import MergeRequest

sys.path.insert(0, os.path.abspath(settings.BASE_DIR))


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    a memory database is setup automatically by django,
    the schema is created so no need to run migration
    """
    with django_db_blocker.unblock():
        call_command("migrate", interactive=False)
        # use seed_data to be explict about what test data is being used
        # call_command("loaddata", "test_data/test_db.json")
        seed_data()


@pytest.fixture(scope="session")
def gitlab():
    private_token = os.environ.get("GITLAB_TOKEN")
    if private_token:
        yield Gitlab("https://gitlab.com", private_token=private_token, per_page=100)
    else:
        yield None


@pytest.fixture(scope="session")
def github():
    access_token = os.environ.get("GITHUB_TOKEN")
    if access_token:
        yield Github(auth=Auth.Token(access_token))
    else:
        yield Github()


@pytest.fixture(scope="session")
def gitlab_test_repo():
    return "vino9/test-project-1"


@pytest.fixture(scope="session")
def github_test_repo():
    return "sloppycoder/hello"


@pytest.fixture
def local_repo(tmp_path):
    repo_base = tempfile.mkdtemp(dir=tmp_path)
    zip_file_path = os.path.abspath(settings.BASE_DIR / "test_data/test_repos.zip")
    with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
        zip_ref.extractall(repo_base)

    yield repo_base

    shutil.rmtree(repo_base)


def seed_data():
    from indexer.models import Author, Commit, CommittedFile, Repository  # noqa: E402

    me, _ = Author.objects.get_or_create(name="me", email="mini@me", real_name="me", real_email="mini@me")

    now = datetime.now().replace(tzinfo=timezone.utc)
    commit1, _ = Commit.objects.get_or_create(sha="feb3a2837630c0e51447fc1d7e68d86f964a8440", author=me, created_at=now)
    commit2, _ = Commit.objects.get_or_create(sha="ee474544052762d314756bb7439d6dab73221d3d", author=me, created_at=now)
    commit3, _ = Commit.objects.get_or_create(sha="e2c8b79813b95c93e5b06c5a82e4c417d5020762", author=me, created_at=now)

    repo1, _ = Repository.objects.get_or_create(clone_url="https://github.com/super/repo.git", repo_type="github")
    repo2, _ = Repository.objects.get_or_create(clone_url="https://gitlab.com/dummy/repo.git", repo_type="gitlab")

    repo1.commits.set([commit1, commit2])
    repo2.commits.set([commit1, commit3])

    commit1.repos.set([repo1, repo2])
    commit2.repos.set([repo1])
    commit3.repos.set([repo2])

    CommittedFile.objects.get_or_create(file_path="README.md", file_name="README.md", change_type="ADD", commit=commit1)
    CommittedFile.objects.get_or_create(
        file_path="package.json", file_name="package.json", change_type="UPDATE", commit=commit1
    )
    CommittedFile.objects.get_or_create(
        file_path="/src/main/java/com/company/MainApplication.java",
        file_name="MainApplication.java",
        change_type="DELETE",
        commit=commit2,
    )
    CommittedFile.objects.get_or_create(
        file_path="app/App.js", file_name="App.js", change_type="UPDATE", commit=commit1
    )

    MergeRequest.objects.create(
        request_id="MR1",
        title="Merge Request 1",
        source_branch="feature/feature-1",
        target_branch="develop",
        repo=repo1,
    )

    MergeRequest.objects.create(
        request_id="MR2",
        title="Merge Request 2",
        source_branch="feature/feature-2",
        target_branch="develop",
        repo=repo1,
    )
