import os
import shlex
import subprocess
import sys
from functools import partial

from django.core.management.base import BaseCommand

from indexer.utils import (
    clone_url2mirror_path,
    display_url,
    enumerate_github_repos,
    enumerate_gitlab_repos,
    match_any,
    redact_http_url,
)


def run(command: str, dry_run: bool) -> int:
    cwd = os.getcwd()
    print(f"pwd={cwd}\n{command}")

    if dry_run:
        return True

    ret = subprocess.call(shlex.split(command))
    if ret == 0:
        return True
    else:
        print(f"*** return code {ret}", file=sys.stderr)
        return False


def mirror_repo(clone_url: str, dest_path: str, dry_run: bool = False, overwrite: bool = False) -> int:
    """
    create a local mirror (as a bare repo) of a remote repo
    """
    parent_dir, repo_dir = clone_url2mirror_path(clone_url, dest_path)
    log_url = display_url(redact_http_url(clone_url))

    cwd = os.getcwd()
    try:
        if os.path.isdir(parent_dir):
            os.chdir(parent_dir)
            if os.path.isdir(f"{repo_dir}/objects"):
                os.chdir(repo_dir)
                return run("git fetch --prune", dry_run)
            else:
                if os.path.isdir(repo_dir):
                    if overwrite:
                        run(f"rm -rf {repo_dir}", dry_run)
                    else:
                        print(f"*** {repo_dir}.git exists, skipping...")
                        return False
        else:
            run(f"mkdir -p {parent_dir}", dry_run)

        if not dry_run:
            os.chdir(parent_dir)
        return run(f"git clone --mirror {log_url}", dry_run)

    finally:
        os.chdir(cwd)


class Command(BaseCommand):
    requires_migrations_checks = True
    help = "Mirror remote repositories to local directory"  # noqa: A003,VNE003

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            default=False,
            help="Overwrite existing repo directory",
        )
        parser.add_argument(
            "--filter",
            dest="filter",
            required=False,
            default="*",
            help="Match repository patterns",
        )
        parser.add_argument(
            "--query",
            dest="query",
            required=False,
            default="",
            help="Query for Github or Gitlab. For local repos, the base path",
        )
        parser.add_argument(
            "--source",
            dest="source",
            required=True,
            help="source of repositories, e.g. local, github, gitlab",
        )
        parser.add_argument(
            "--output",
            dest="output",
            required=True,
            help="Output directory",
        )

    def handle(self, *args, **options):
        source = options["source"]
        output = options["output"]

        if source == "gitlab":
            enumerator = partial(enumerate_gitlab_repos)
        elif source == "github":
            enumerator = partial(enumerate_github_repos)
        else:  # pragma: no cover
            print("don't nkow how to mirror local repos")
            return None

        for repo_url, _ in enumerator(options["query"]):
            if match_any(repo_url, options["filter"]):
                print(f"Mirroring {repo_url} to {output}")
                mirror_repo(repo_url, output, options["dry_run"], options["overwrite"])
