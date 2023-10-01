import os
from functools import partial
from typing import Iterator

from django.core.management.base import BaseCommand

from indexer.utils import (
    enumerate_github_repos,
    enumerate_gitlab_repos,
    enumerate_local_repos,
    log,
    match_any,
    upload_file,
)
from indexer.worker import (
    export_all_data,
    index_commits,
    index_github_merge_requests,
    index_gitlab_merge_requests,
    update_commit_stats,
)


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
            "--merge_requests_only",
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
            "--mode",
            dest="query",
            required=False,
            default="commits",
            help="commits",
        )
        parser.add_argument(
            "--source",
            dest="source",
            required=True,
            help="source of repositories, e.g. local, github, gitlab",
        )
        parser.add_argument(
            "--export-csv",
            dest="export_csv",
            default="",
            help="Export index result to CSV file",
        )
        parser.add_argument(
            "--upload",
            action="store_true",
            default=False,
        )

    def handle(self, *args, **options):
        n_repos, n_commits, n_merge_quests = 0, 0, 0

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
            for repo_url, project in enumerator(query):
                if match_any(repo_url, options["filter"]):
                    if not options["dry_run"]:
                        source = "other" if source == "list" else source
                        if options["merge_requests_only"]:
                            if source == "gitlab":
                                n_merge_quests += index_gitlab_merge_requests(project, show_progress=True)
                            elif source == "github":
                                n_merge_quests += index_github_merge_requests(project, show_progress=True)
                            else:
                                print(f"don't know how to index merge_request for {source}")
                        else:
                            n_commits += index_commits(repo_url, source, show_progress=True)
                        n_repos += 1

        if n_commits or query == "_stats_":
            update_commit_stats()

        log(f"finished indexing {n_commits} commits in {n_repos} repositories")

        csv_file = options["export_csv"]
        if csv_file:
            export_all_data(csv_file)

            if options["upload"] and os.path.exists(csv_file) and os.stat(csv_file).st_size > 0:
                upload_file(csv_file, os.path.basename(csv_file))
