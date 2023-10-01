import os
import re

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from indexer.utils import redact_http_url

_REPO_TYPES_ = ["gitlab", "gitlab_private", "github", "bitbucket", "bitbucket_private", "local", "other"]


class Author(models.Model):
    class Meta(TypedModelMeta):
        db_table = "authors"

    name = models.CharField(max_length=128)
    email = models.CharField(max_length=1024)
    real_name = models.CharField(max_length=128)
    real_email = models.CharField(max_length=1024)
    company = models.CharField(max_length=64, null=True)
    team = models.CharField(max_length=64, null=True)
    author_group = models.CharField(max_length=64, null=True)
    login_name = models.CharField(max_length=128, null=True)

    def __str__(self) -> str:
        return f"Author(id={self.id}, email={self.email}, real_email={self.real_email}"


class Repository(models.Model):
    class Meta(TypedModelMeta):
        db_table = "repositories"
        verbose_name_plural = "repositories"

    repo_type = models.CharField(max_length=20)
    repo_name = models.CharField(max_length=128)
    repo_group = models.CharField(max_length=64, null=True)
    component = models.CharField(max_length=64, null=True)
    clone_url = models.CharField(max_length=256)
    is_active = models.BooleanField(default=True)
    last_indexed_at = models.CharField(max_length=32, null=True)
    last_commit_at = models.CharField(max_length=32, null=True)

    # relationships
    commits = models.ManyToManyField(
        "Commit",
        through="RepositoryCommitLink",
        through_fields=("repo", "commit"),
    )

    # updated 2023-09-28:
    # remove ssh support for clone_url, only http is supported
    # browse_url is converted to a propery
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.clone_url.startswith("git@"):
            raise ValueError("ssh clone url is not supported")

        # if it's an existing record, do nothing
        if self.id:
            return

        if self.repo_type and self.repo_type not in _REPO_TYPES_:
            raise ValueError(f"repo_type must be one of {_REPO_TYPES_}")

        # try to determine repo_type when not provided
        if self.repo_type is None:
            if self.clone_url.startswith("http"):
                # remote repo
                if "gitlab" in self.clone_url:
                    self.repo_type = "gitlab"
                elif "github.com" in self.clone_url:
                    self.repo_type = "github"
                elif "bitbucket.com" in self.clone_url:
                    self.repo_type = "bitbucket"
            else:
                self.repo_type = "local"

        name = os.path.basename(self.clone_url)  # works for both http and git@ style url
        self.repo_name = re.sub(r".git$", "", name)

    @property
    def browse_url(self) -> str:
        if self.repo_type == "local":
            return "http://localhost:9000/gitweb/"
        else:
            return re.sub(r".git$", "", self.clone_url)

    @property
    def url_for_commit(self) -> str:
        """return the url that display the commit details"""
        if self.repo_type == "github":
            return f"{self.browse_url}/commit"
        elif self.repo_type.startswith("gitlab"):
            return f"{self.browse_url}/-/commit"
        elif self.repo_type.startswith("bitbucket"):
            return f"{self.browse_url}/commits"
        else:
            return ""

    def __str__(self) -> str:
        return f"Repository(id={self.id}, url={self.clone_url})"


class Commit(models.Model):
    class Meta(TypedModelMeta):
        db_table = "commits"

    sha = models.CharField(max_length=40, primary_key=True)
    branches = models.CharField(max_length=1024, default="")
    message = models.CharField(max_length=2048, default="")
    created_at = models.CharField(max_length=32)
    created_ts = models.DateTimeField(null=True)

    # metrics by pydriller
    is_merge = models.BooleanField(default=False)
    n_lines = models.IntegerField(default=0)
    n_files = models.IntegerField(default=0)
    n_insertions = models.IntegerField(default=0)
    n_deletions = models.IntegerField(default=0)
    dmm_unit_size = models.FloatField(default=0.0)
    dmm_unit_complexity = models.FloatField(default=0.0)
    dmm_unit_interfacing = models.FloatField(default=0.0)
    # should be populated from committed_files
    n_lines_changed = models.IntegerField(default=0)
    n_lines_ignored = models.IntegerField(default=0)
    n_files_changed = models.IntegerField(default=0)
    n_files_ignored = models.IntegerField(default=0)

    # relationships
    author = models.ForeignKey(Author, related_name="commits", on_delete=models.PROTECT)
    repos = models.ManyToManyField(
        Repository,
        through="RepositoryCommitLink",
        through_fields=("commit", "repo"),
    )

    def __str__(self) -> str:
        return f"Commit(id={self.sha} by Author(id={self.author.id}"


class CommittedFile(models.Model):
    class Meta(TypedModelMeta):
        db_table = "committed_files"

    commit_sha = models.CharField(max_length=40)
    change_type = models.CharField(max_length=16, default="UNKNOWN")
    file_path = models.CharField(max_length=256)
    file_name = models.CharField(max_length=128)
    file_type = models.CharField(max_length=128)

    # line metrics from Pydiller
    n_lines_added = models.IntegerField(default=0)
    n_lines_deleted = models.IntegerField(default=0)
    n_lines_changed = models.IntegerField(default=0)
    n_lines_of_code = models.IntegerField(default=0)
    # metho metrics from pydriller
    n_methods = models.IntegerField(default=0)
    n_methods_changed = models.IntegerField(default=0)
    is_on_exclude_list = models.BooleanField(default=False)
    is_superfluous = models.BooleanField(default=False)

    # relationships
    commit = models.ForeignKey(Commit, related_name="files", on_delete=models.CASCADE)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.id:
            return

        main, ext = os.path.splitext(self.file_path)
        if main.startswith("."):
            self.file_type = "hiden"
        elif ext != "":
            self.file_type = ext[1:].lower()
        else:
            self.file_type = "generic"

    def __str__(self) -> str:
        return f"CommittedFile(id={self.id} part of Commit({self.commit.sha}"


class RepositoryCommitLink(models.Model):
    class Meta(TypedModelMeta):
        # table name is chosen to be compatible with existing schema predates this project
        db_table = "repo_to_commits"

    commit = models.ForeignKey(Commit, on_delete=models.DO_NOTHING)
    repo = models.ForeignKey(Repository, on_delete=models.DO_NOTHING)


class MergeRequest(models.Model):
    class Meta(TypedModelMeta):
        db_table = "merge_requests"

    request_id = models.CharField(max_length=40)
    title = models.CharField(max_length=1024)
    state = models.CharField(max_length=32)

    source_sha = models.CharField(max_length=256, default="")
    source_branch = models.CharField(max_length=256, default="")
    target_branch = models.CharField(max_length=256, null=True, default="")
    merge_sha = models.CharField(max_length=256, null=True, default="")

    created_at = models.CharField(max_length=32)
    merged_at = models.CharField(max_length=32, null=True)
    updated_at = models.CharField(max_length=32, null=True)
    first_comment_at = models.CharField(max_length=32, null=True)

    is_merged = models.BooleanField(default=False)
    merged_by_username = models.CharField(max_length=32, null=True)

    has_tests = models.BooleanField(default=False)
    has_test_passed = models.BooleanField(default=False)

    # relationships
    repo = models.ForeignKey(Repository, related_name="merge_requests", on_delete=models.CASCADE)


def ensure_repository(url: str, repo_type: str) -> Repository:
    base_url = redact_http_url(url)
    repo, _ = Repository.objects.get_or_create(clone_url=base_url, repo_type=repo_type)
    return repo
