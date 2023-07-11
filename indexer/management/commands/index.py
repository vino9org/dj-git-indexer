from functools import partial
from typing import Iterator

from django.core.management.base import BaseCommand

from indexer.utils import (
    enumerate_github_repos,
    enumerate_gitlab_repos,
    enumerate_local_repos,
    log,
    match_any,
)
from indexer.worker import index_repository, update_commit_stats


def enumberate_from_file(source_file: str, query: str) -> Iterator[str]:
    with open(source_file, "r") as f:
        for line in f.readlines():
            line = line.strip()
            if not line.startswith("#") and len(line) > 6:
                yield line.strip()


class Command(BaseCommand):
    requires_migrations_checks = True
    help = "Index the git repositories and extract commit information"  # noqa: A003,VNE003,E501

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
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

    def handle(self, *args, **options):
        # the sqlite3 database this program needs will reside in memory
        # for performance reason as well as ability to run in serverless environment
        # we'll load the database from disk if it exists
        # after indexing is done we'll save the database in memory back to disk
        n_repos, n_commits = 0, 0

        source = options["source"]
        query = options["query"]

        if source == "gitlab":
            enumerator = partial(enumerate_gitlab_repos)
        elif source == "github":
            enumerator = partial(enumerate_github_repos)
        elif source == "local":
            enumerator = partial(enumerate_local_repos)
        elif source == "list":
            enumerator = partial(enumberate_from_file, query)
        else:
            print(f"don't know how to index {source}")
            return

        # speical undocumented query string for update the stats only
        # do not index any repos
        if query != "_stats_":
            for repo_url in enumerator(query):
                if match_any(repo_url, options["filter"]):
                    if not options["dry_run"]:
                        source = "other" if source == "list" else source
                        n_commits += index_repository(repo_url, source, show_progress=True)
                        n_repos += 1

        if n_commits or query == "_stats_":
            update_commit_stats()

        log(f"finished indexing {n_commits} commits in {n_repos} repositories")
