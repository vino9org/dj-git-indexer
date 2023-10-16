import os
import random
import string
from datetime import datetime

import git
import pytest
from django.utils.timezone import make_aware

from indexer.models import Repository, RepositoryCommitLink, ensure_repository
from indexer.worker import (
    index_commits,
    index_github_pull_requests,
    index_gitlab_merge_requests,
)


def test_index_github_repo(db, github_test_repo):
    assert index_commits(f"https://github.com/{github_test_repo}.git") > 3


@pytest.mark.skipif(os.environ.get("GITLAB_TOKEN") is None, reason="gitlab token not available")
def test_index_gitlab_repo(db, gitlab_test_repo):
    assert index_commits(f"https://gitlab.com/{gitlab_test_repo}") > 0


@pytest.mark.skipif(os.environ.get("GITLAB_TOKEN") is None, reason="gitlab token not available")
def test_index_gitlab_merge_requests(db, gitlab, gitlab_test_repo):
    project = gitlab.projects.get(gitlab_test_repo)
    assert index_gitlab_merge_requests(project) > 0

    repo = Repository.objects.get(clone_url=project.http_url_to_repo, repo_type="gitlab")
    assert repo is not None
    mr = repo.merge_requests.filter(repo=repo, request_id="1").first()
    assert mr.request_id == "1" and mr.state == "merged" and mr.target_branch == "main"


def test_index_github_pull_requests(db, github, github_test_repo):
    repo = github.get_repo(github_test_repo)
    assert index_github_pull_requests(repo) > 0

    repo = Repository.objects.get(clone_url=repo.clone_url, repo_type="github")
    assert repo is not None
    pr = repo.merge_requests.filter(repo=repo, request_id="1").first()
    assert pr.request_id == "1" and pr.state == "closed" and pr.is_merged


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
    assert index_commits(repo1, "local") == 2
    repo1_sha = repo_hashes(repo1)
    assert len(repo1_sha) == 2

    # index a clone shouldn't create new commits that is in the original repo
    # this is the known timestamp in the test repo
    known_last_commit_dt = datetime.strptime("2023-07-07T15:59:06+08:00", "%Y-%m-%dT%H:%M:%S%z")

    repo1_clone = local_repo + "/repo1_clone"
    assert index_commits(repo1_clone, "local") == 3
    repo1_clone_sha = repo_hashes(repo1_clone)
    assert len(repo1_clone_sha) == 3

    # after index the repo object in db should have valid timestamps
    repo1_clone_obj = ensure_repository(repo1_clone, "local")
    assert repo1_clone_obj.last_indexed_at
    assert repo1_clone_obj.last_commit_at == known_last_commit_dt

    # index the same repo again, the last_commit_at should be updated
    # new commits will be indexed
    new_commit_dt = make_aware(datetime.now())
    n_new_commits = _add_random_commit_(repo1_clone)
    assert index_commits(repo1_clone, "local") == n_new_commits
    repo1_clone_obj.refresh_from_db()
    assert abs((repo1_clone_obj.last_commit_at - new_commit_dt).total_seconds()) < 60

    # empty repo should not throw any exception
    empty_repo = local_repo + "/empty_repo"
    assert index_commits(empty_repo, "local") == 0

    # index a repo for the 2nd time should not increase the number of commits
    assert index_commits(repo1, "local") == 0
    repo1_sha = repo_hashes(repo1)
    assert len(repo1_sha) == 2

    # check the final record numbers in the database
    assert all(sha in repo1_clone_sha for sha in repo1_sha)

    rows_after = RepositoryCommitLink.objects.filter().count()
    assert rows_after - rows_before == 5 + n_new_commits


def repo_hashes(repo_url):
    repo = Repository.objects.get(clone_url=repo_url, repo_type="local")
    hashes = [c.sha for c in repo.commits.all()]
    # does a unique then return. technically not needed
    return list(set(hashes))


def _add_random_commit_(repo_path: str):
    """create a few random commit into a local repo"""
    n_rand = random.randint(2, 6)
    print(f"*** adding {n_rand} random commits ****")

    for _ in range(n_rand):
        random_str = "".join(random.choice(string.ascii_lowercase) for i in range(3))
        with open(repo_path + f"/random{random_str}.txt", "w") as f:
            f.write(f"random content:{random_str}")

        repo = git.Repo(repo_path)
        repo.git.add(update=True)  # Equivalent to `git add -u`
        repo.git.add(A=True)  # To also add untracked files, equivalent to `git add .`
        repo.index.commit("some random commit")

    return n_rand
