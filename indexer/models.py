import os
import re
from typing import List

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from .utils import clone_to_browse_url

_REPO_TYPES_ = ["gitlab", "gitlab_private", "github", "bitbucket", "bitbucket_private", "local", "other"]


class Author(models.Model):
    class Meta(TypedModelMeta):
        db_table = "authors"

    name: str = models.CharField(max_length=128)
    email: str = models.CharField(max_length=1024)
    real_name: str = models.CharField(max_length=128)
    real_email: str = models.CharField(max_length=1024)
    company: str = models.CharField(max_length=64, null=True)
    team: str = models.CharField(max_length=64, null=True)
    author_group: str = models.CharField(max_length=64, null=True)

    def __str__(self) -> str:
        return f"Author(id={self.id}, email={self.email}, real_email={self.real_email}"


class Repository(models.Model):
    class Meta(TypedModelMeta):
        db_table = "repositories"

    repo_type: str = models.CharField(max_length=20)
    repo_name: str = models.CharField(max_length=128)
    repo_group: str = models.CharField(max_length=64, null=True)
    component: str = models.CharField(max_length=64, null=True)
    clone_url: str = models.CharField(max_length=256)
    browse_url: str = models.CharField(max_length=256)
    is_active: bool = models.BooleanField(default=True)
    last_indexed_at: str = models.CharField(max_length=32, null=True)
    last_commit_at: str = models.CharField(max_length=32, null=True)

    # relationships
    commits = models.ManyToManyField(
        "Commit",
        through="RepositoryCommitLink",
        through_fields=("repo", "commit"),
    )

    # create a constructor to set browse_url based on clone_url
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # if it's an existing record, do nothing
        if self.id:
            return

        if self.repo_type and self.repo_type not in _REPO_TYPES_:
            raise ValueError(f"repo_type must be one of {_REPO_TYPES_}")

        # try to determine repo_type is not provided
        if not self.repo_type:
            if self.clone_url.startswith("http") or self.clone_url.startswith("git@"):
                # remote repo
                if "gitlab" in self.clone_url:
                    self.repo_type = "gitlab"
                elif "github.com" in self.clone_url:
                    self.repo_type = "github"
                elif "bitbucket.com" in self.clone_url:
                    self.repo_type = "bitbucket"
            else:
                self.repo_type = "local"

        if self.repo_type == "local":
            self.browse_url = "http://localhost:9000/gitweb/"
        else:
            self.browse_url = clone_to_browse_url(self.clone_url)

        name = os.path.basename(self.clone_url)  # works for both http and git@ style url
        self.repo_name = re.sub(r".git$", "", name)

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
        return f"Repository(id={self.id}, url={self.browse_url}, clone_url={self.clone_url})"


class Commit(models.Model):
    class Meta(TypedModelMeta):
        db_table = "commits"

    sha: str = models.CharField(max_length=40, primary_key=True)
    branches: str = models.CharField(max_length=1024, default="")
    message: str = models.CharField(max_length=2048, default="")
    created_at: str = models.CharField(max_length=32)

    # metrics by pydriller
    is_merge: bool = models.BooleanField(default=False)
    n_lines: int = models.IntegerField(default=0)
    n_files: int = models.IntegerField(default=0)
    n_insertions: int = models.IntegerField(default=0)
    n_deletions: int = models.IntegerField(default=0)
    dmm_unit_size: float = models.FloatField(default=0.0)
    dmm_unit_complexity: float = models.FloatField(default=0.0)
    dmm_unit_interfacing: float = models.FloatField(default=0.0)
    # should be populated from committed_files
    n_lines_changed: int = models.IntegerField(default=0)
    n_lines_ignored: int = models.IntegerField(default=0)
    n_files_changed: int = models.IntegerField(default=0)
    n_files_ignored: int = models.IntegerField(default=0)

    # relationships
    author: Author = models.ForeignKey(Author, related_name="commits", on_delete=models.PROTECT)
    repos: List[Repository] = models.ManyToManyField(
        Repository,
        through="RepositoryCommitLink",
        through_fields=("commit", "repo"),
    )

    def __str__(self) -> str:
        return f"Commit(id={self.sha} by Author(id={self.author.id}"


class CommittedFile(models.Model):
    class Meta(TypedModelMeta):
        db_table = "committed_files"

    commit_sha: str = models.CharField(max_length=40)
    change_type: str = models.CharField(max_length=16, default="UNKNOWN")
    file_path: str = models.CharField(max_length=256)
    file_name: str = models.CharField(max_length=128)
    file_type: str = models.CharField(max_length=128)

    # line metrics from Pydiller
    n_lines_added: int = models.IntegerField(default=0)
    n_lines_deleted: int = models.IntegerField(default=0)
    n_lines_changed: int = models.IntegerField(default=0)
    n_lines_of_code: int = models.IntegerField(default=0)
    # metho metrics from pydriller
    n_methods: int = models.IntegerField(default=0)
    n_methods_changed: int = models.IntegerField(default=0)
    is_on_exclude_list: bool = models.BooleanField(default=False)
    is_superfluous: bool = models.BooleanField(default=False)

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

    commit: Commit = models.ForeignKey(Commit, on_delete=models.DO_NOTHING)
    repo: Repository = models.ForeignKey(Repository, on_delete=models.DO_NOTHING)
