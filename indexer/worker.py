import csv
import os
import sqlite3
import traceback
from datetime import datetime

from django.db import DatabaseError, connection
from git.exc import GitCommandError
from gitlab.v4.objects import projects
from pydriller import Repository as PyDrillerRepository
from pydriller.domain.commit import Commit as PyDrillerCommit

from .models import Author, Commit, CommittedFile, MergeRequest, ensure_repository
from .sql import QUERY_SQL, STATS_SQL
from .utils import (
    display_url,
    gitlab_timestamp_to_iso,
    log,
    normalize_branches,
    redact_http_url,
    should_exclude_from_stats,
)

GITLAB_TIMETSAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def index_commits(clone_url: str, git_repo_type: str = "", show_progress: bool = False, timeout: int = 28800) -> int:
    n_branch_updates, n_new_commits = 0, 0
    log_url = display_url(redact_http_url(clone_url))

    try:
        repo = ensure_repository(clone_url, git_repo_type)
        if repo is None:
            log(f"### cannot create repostitory object for {log_url}")
            return 0

        if repo.is_active is False:
            log(f"### skipping inactive repository {log_url}")
            return 0

        log(f"starting to index {log_url}")
        start_t = datetime.now()

        # use list comprehension to force loading of commits
        old_commits = {}
        for commit in repo.commits.all():
            old_commits[commit.sha] = commit

        for git_commit in PyDrillerRepository(clone_url, include_refs=True, include_remotes=True).traverse_commits():
            # impose some timeout to avoid spending tons of time on very large repositories
            if (datetime.now() - start_t).seconds > timeout:  # pragma: no cover
                print(f"### indexing not done after {timeout} seconds, aborting {log_url}")
                break

            if git_commit.hash in old_commits:
                # we've seen this commit before, just compare branches and update
                # if needed
                commit = old_commits[git_commit.hash]
                new_branches = normalize_branches(git_commit.branches)
                if new_branches != commit.branches:
                    commit.branches = new_branches
                    commit.save()
                    n_branch_updates += 1
            else:
                # check if the same repo is already linked to another repo
                try:
                    commit = Commit.objects.get(sha=git_commit.hash)
                except Commit.DoesNotExist:
                    commit = _new_commit_(git_commit)
                repo.commits.add(commit)
                n_new_commits += 1

            nn = n_new_commits + n_branch_updates
            if nn > 0 and nn % 200 == 0 and show_progress:
                log(f"indexed {n_new_commits:5,} new commits and {n_branch_updates:5,} branch updates")

        repo.last_indexed_at = datetime.now().astimezone().isoformat(timespec="seconds")

        if (n_new_commits + n_branch_updates) > 0:
            log(f"indexed {n_new_commits:5,} new commits and {n_branch_updates:5,} branch updates in the repository")

        return n_new_commits + n_branch_updates

    except GitCommandError as e:
        print(f"{e._cmdline} returned {e.stderr} for {log_url}")
    except DatabaseError as e:
        exc = traceback.format_exc()
        print(f"DatabaseError indexing repository {log_url} => {str(e)}\n{exc}")
    except Exception as e:  # pragma: no cover
        exc = traceback.format_exc()
        print(f"Exception indexing repository {log_url} => {str(e)}\n{exc}")

    return 0


def index_gitlab_merge_requests(project: projects.Project, show_progress: bool = False) -> int:
    n_requests = 0
    log_url = display_url(project.http_url_to_repo)

    try:
        repo = ensure_repository(project.http_url_to_repo, "gitlab")
        if repo is None:
            log(f"### cannot create repostitory object for {log_url}")
            return 0

        if repo.is_active is False:
            log(f"### skipping inactive repository {log_url}")
            return 0

        log(f"starting to index merge requests for {log_url}")

        merge_requests = project.mergerequests.list(all=True)
        for mr in merge_requests:
            mr_id = mr.get_id()

            if mr.state not in ["closed", "merged"]:
                # index only closed or merged merge requests
                continue

            db_obj = MergeRequest.objects.filter(request_id=mr_id, repo=repo).first()
            if db_obj is not None:
                # merge request already indexed
                continue

            is_merged, merged_by_username, merge_commit_sha = False, None, None
            if mr.state == "merged":
                is_merged, merged_by_username = True, mr.merge_user["username"]
                merge_commit_sha = mr.squash_commit_sha if mr.squash else mr.merge_commit_sha

            MergeRequest.objects.create(
                repo=repo,
                request_id=mr_id,
                state=mr.state,
                source_branch=mr.source_branch,
                target_branch=mr.target_branch,
                source_sha=mr.sha,
                merge_sha=merge_commit_sha,
                created_at=gitlab_timestamp_to_iso(mr.created_at),
                merged_at=gitlab_timestamp_to_iso(mr.merged_at),
                updated_at=gitlab_timestamp_to_iso(mr.updated_at),
                # first_comment_at = models.CharField(max_length=32)
                is_merged=is_merged,
                merged_by_username=merged_by_username,
            ).save()

            n_requests += 1

            if n_requests > 0 and n_requests % 50 == 0 and show_progress:
                log(f"indexed {n_requests:3,} merge requests ")

        if n_requests > 0:
            log(f"indexed {n_requests:3,} merge requests in the repository")

        return n_requests

    except GitCommandError as e:
        print(f"{e._cmdline} returned {e.stderr} for {log_url}")
    except DatabaseError as e:
        exc = traceback.format_exc()
        print(f"DatabaseError indexing repository {log_url} => {str(e)}\n{exc}")
    except Exception as e:  # pragma: no cover
        exc = traceback.format_exc()
        print(f"Exception indexing repository {log_url} => {str(e)}\n{exc}")

    return 0


def index_github_merge_requests(project: projects.Project, show_progress: bool = False) -> int:
    return 0


def update_commit_stats() -> None:
    """update stats at commit level"""
    log("updating commit stats")
    cursor = connection.cursor()
    for statement in STATS_SQL:
        try:
            cursor.execute(statement)
        except DatabaseError as e:
            exc = traceback.format_exc()
            print(f"Exception execute statement {statement} => {str(e)}\n{exc}")


def _new_commit_(git_commit: PyDrillerCommit) -> Commit:
    author, created = Author.objects.get_or_create(
        name=git_commit.committer.name.lower(),
        email=git_commit.committer.email.lower(),
    )
    if created:
        author.real_name = author.name
        author.real_email = author.email
        author.save()

    commit = Commit(
        sha=git_commit.hash,
        message=git_commit.msg[:2048],  # some commits has super long message, e.g. squash merge
        author=author,
        is_merge=git_commit.merge,
        branches=normalize_branches(git_commit.branches),
        n_lines=git_commit.lines,
        n_files=git_commit.files,
        n_insertions=git_commit.insertions,
        n_deletions=git_commit.deletions,
        # comment to save some time. metrics not used for now
        # dmm_unit_size=git_commit.dmm_unit_size,
        # dmm_unit_complexity=git_commit.dmm_unit_complexity,
        # dmm_unit_interfacing=git_commit.dmm_unit_interfacing,
        created_at=git_commit.committer_date.isoformat(timespec="seconds"),
        created_ts=git_commit.committer_date,
    )
    commit.save()

    for mod in git_commit.modified_files:
        file_path = mod.new_path or mod.old_path
        flag = should_exclude_from_stats(file_path)
        new_file = CommittedFile(
            commit_sha=git_commit.hash,
            change_type=str(mod.change_type).split(".")[1],  # enum ModificationType.ADD => "ADD"
            file_path=file_path,
            file_name=mod.filename,
            n_lines_added=mod.added_lines,
            n_lines_deleted=mod.deleted_lines,
            n_lines_changed=mod.added_lines + mod.deleted_lines,
            n_lines_of_code=mod.nloc if mod.nloc else 0,
            n_methods=len(mod.methods),
            n_methods_changed=len(mod.changed_methods),
            is_on_exclude_list=flag,
            is_superfluous=flag,
            commit=commit,
        )
        new_file.save()

    return commit


def export_all_data(csv_file: str) -> None:
    cursor = connection.cursor()
    result = cursor.execute(QUERY_SQL["all_commit_data"])
    columns = [col[0] for col in cursor.description]

    n_rows = 0
    with open(csv_file, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(columns)
        for row in result.fetchall():
            n_rows += 1
            writer.writerow(row)
        log(f"exported {n_rows} rows to {csv_file}")


def export_db(dbf: str):
    if "sqlite" not in connection._connections.settings[connection._alias]["ENGINE"]:  # type: ignore
        log("not a sqlite database, not exporting")
        return

    # export database to file
    # write to temp file first then rename to avoid potentially corrupting the database
    tmp_file = dbf + ".new"
    file_conn = sqlite3.connect(tmp_file)
    connection.cursor().connection.backup(file_conn)
    file_conn.close()

    if dbf and os.path.exists(dbf):
        os.unlink(dbf)
    os.rename(tmp_file, dbf)
    log(f"saved database to {dbf}")
