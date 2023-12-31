import os
import shlex

import pytest
from django.core.management import call_command

from indexer.management.commands.index import enumberate_from_file
from indexer.worker import export_all_data, update_commit_stats


def invoke_command(cmdline: str) -> None:
    argv = shlex.split(cmdline)
    # for now this does not work, need rewrite in commands
    call_command(argv[0], argv[1:])


@pytest.mark.skipif(os.environ.get("GITHUB_TOKEN") is not None, reason="does not work in Github action, no ssh key")
def test_run_mirror(db, tmp_path, github_test_repo, capfd):
    cmdline = (
        f"mirror --query {github_test_repo} --source github --filter * --output {tmp_path.as_posix()}/ --overwrite"
    )

    # 1st run should trigger a git clone
    invoke_command(cmdline)
    captured = capfd.readouterr()
    assert "git clone --mirror" in captured.out

    invoke_command(cmdline)
    captured = capfd.readouterr()
    assert "git fetch --prune" in captured.out


@pytest.mark.skipif(os.environ.get("GITHUB_TOKEN") is not None, reason="does not work in Github action, no ssh key")
def test_run_indexer(db, tmp_path, github_test_repo):
    cmdline = f"index --query {github_test_repo} --source github --filter *"
    invoke_command(cmdline)


def test_enumberate_from_file(tmp_path):
    repo_lst = str(tmp_path / "repos.txt")
    with open(repo_lst, "w") as f:
        f.write("/user/repo1.git\n")
        f.write("#/user/repo2.git\n")

    repos = list(enumberate_from_file(repo_lst, ""))
    assert len(repos) == 1 and "repo1" in repos[0]


def test_export_csv(tmp_path, db):
    update_commit_stats()  # this creates the view we need
    tmp_f = (tmp_path / "test.csv").as_posix()
    export_all_data(tmp_f)
    assert os.path.isfile(tmp_f) and os.stat(tmp_f).st_size > 0
