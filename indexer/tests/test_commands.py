import os
import shlex
from io import StringIO

import pytest
from django.core.management import call_command

from indexer.management.commands.index import enumberate_from_file


def invoke_command(cmdline: str) -> str:
    argv = shlex.split(cmdline)
    stdout = StringIO()
    # for now this does not work, need rewrite in commands
    call_command(argv[0], argv[1:], stdout=stdout)
    return stdout.getvalue()


@pytest.mark.skipif(os.environ.get("GITHUB_TOKEN") is not None, reason="does not work in Github action, no ssh key")
def test_run_mirror(db, tmp_path, github_test_repo):
    cmdline = (
        f"mirror --query {github_test_repo} --source github --filter * --output {tmp_path.as_posix()}/ --overwrite"
    )

    # 1st run should trigger a git clone
    invoke_command(cmdline)
    # assert "git clone --mirror" in out1

    invoke_command(cmdline)
    # assert "git fetch --prune" in out2


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
