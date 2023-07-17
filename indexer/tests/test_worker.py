import os

import pytest

from indexer.models import Repository, RepositoryCommitLink
from indexer.worker import export_db, index_repository


def test_index_github_repo(db, github_test_repo):
    assert index_repository(f"https://github.com/{github_test_repo}.git") > 3


@pytest.mark.skipif(os.environ.get("GITLAB_TOKEN") is None, reason="gitlab token not available")
def test_index_gitlab_repo(db, gitlab_test_repo):
    assert index_repository(f"https://gitlab.com/vino9/{gitlab_test_repo}") > 0


def test_export_db(db, tmp_path):
    # indexer should already have some data
    tmp_f = (tmp_path / "test.db").as_posix()
    export_db(tmp_f)
    assert os.path.isfile(tmp_f) and os.stat(tmp_f).st_size > 0


def test_index_local_repo(db, local_repo):
    """
    there're 2 test repos
    repo1 has 2 commits
    repo1_clone is a clone of repo1, then add 1 more commits, so totaly 3 commits
    empty_repo is empty, no commit after git init.
    """
    rows_before = RepositoryCommitLink.objects.filter().count()

    # index a new repo for the 1st time
    repo1 = local_repo + "/repo1"
    assert index_repository(repo1, "local") == 2
    repo1_sha = repo_hashes(repo1)
    assert len(repo1_sha) == 2

    # index a clone shouldn't create new commits that is in the original repo
    repo1_clone = local_repo + "/repo1_clone"
    assert index_repository(repo1_clone, "local") == 3
    repo1_clone_sha = repo_hashes(repo1_clone)
    assert len(repo1_clone_sha) == 3

    # empty repo should not throw any exception
    empty_repo = local_repo + "/empty_repo"
    assert index_repository(empty_repo, "local") == 0

    # index a repo for the 2nd time should not increase the number of commits
    assert index_repository(repo1, "local") == 0
    repo1_sha = repo_hashes(repo1)
    assert len(repo1_sha) == 2

    # check the final record numbers in the database
    assert all(sha in repo1_clone_sha for sha in repo1_sha)

    rows_after = RepositoryCommitLink.objects.filter().count()
    assert rows_after - rows_before == 5


def repo_hashes(repo_url):
    repo = Repository.objects.get(clone_url=repo_url, repo_type="local")
    hashes = [c.sha for c in repo.commits.all()]
    # does a unique then return. technically not needed
    return list(set(hashes))
