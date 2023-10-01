import fnmatch
import os
import re
import sys
import warnings
from datetime import datetime
from typing import Any, Iterator, List, Optional, Tuple

import gitlab
import psutil
from git import InvalidGitRepositoryError
from github import Auth, BadCredentialsException, Github
from pydriller.git import Git

# files matches any of the regex will not be counted
# towards commit stats
_IGNORE_PATTERNS_ = [
    re.compile(
        "^(vendor|Pods|target|YoutuOCWrapper|vos-app-protection|vos-processor|\\.idea|\\.vscode)/."  # noqa: E501
    ),
    re.compile("^[a-zA-Z0-9_]*?/Pods/"),
    re.compile("^.*(xcodeproj|xcworkspace)/."),
    re.compile(r".*\.(jar|pbxproj|lock|bk|bak|backup|class|swp|sum|pdf|png)$"),
    re.compile(r"^.*/?package-lock\.json$"),
    re.compile(r"^.*/?(\.next|node_modules|\.devcontainer)(/|$).*"),
    re.compile(r"(^|.*/)_.*\.(js|scss)$"),
]


def timestamp() -> str:
    return datetime.now().isoformat()[:19]


def rss() -> int:
    """return rss memory usage in MB"""
    return int(meminfo().rss / 1024 / 1024)


def meminfo():
    pid = os.getpid()
    proc = psutil.Process(pid)
    return proc.memory_info()


def is_git_repo(path: str) -> bool:
    try:
        repo = Git(path)
        repo.get_head()
        return True
    except InvalidGitRepositoryError:
        return False
    except ValueError:
        # this exception happens when a repo is empty
        return False


def match_any(path: str, patterns: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns.split(","))


def should_exclude_from_stats(path: str) -> bool:
    """
    return true if the path should be ignore
    for calculating commit stats
    """
    for regex in _IGNORE_PATTERNS_:
        if regex.match(path):
            return True
    return False


def enumerate_local_repos(base_dir: str) -> Iterator[Tuple[str, Any]]:
    for root, dirs, _ in os.walk(os.path.expanduser(base_dir), topdown=True):
        if ".git" in dirs:
            dirs.remove(".git")

        for dd in dirs:
            abs_path = os.path.abspath(root + "/" + dd)
            if is_git_repo(abs_path):
                yield abs_path, None


def enumerate_gitlab_repos(
    query: str, private_token: Optional[str] = None, url: str = "https://gitlab.com"
) -> Iterator[Tuple[str, Any]]:
    if private_token is None:
        private_token = os.environ.get("GITLAB_TOKEN")
        if not private_token:
            print("GITLAB_TOKEN environment variable not set")
            sys.exit(1)

    gl = gitlab.Gitlab(url, private_token=private_token, per_page=100)
    for project in gl.search(scope="projects", search=query):
        repo = gl.projects.get(project["id"])
        clone_url = repo.http_url_to_repo
        if repo.visibility == "private":
            clone_url = clone_url.replace("://", f"://oauth2:{private_token}@")
        yield clone_url, repo


def enumerate_github_repos(
    query: str, access_token: Optional[str] = None, useHttpUrl: bool = False
) -> Iterator[Tuple[str, Any]]:
    if access_token is None:
        access_token = os.environ.get("GITHUB_TOKEN")

    try:
        gh = Github(auth=Auth.Token(access_token)) if access_token else Github()
        for repo in gh.search_repositories(query=query):
            clone_url = repo.clone_url
            if repo.private:
                clone_url = clone_url.replace("://", f"://{access_token}:@")
            yield clone_url, repo
    except BadCredentialsException as e:
        print(f"authentication error => {e}")
    except Exception as e:
        print(f"gitlab search {query} error {type(e)} => {e}")


def log(msg: str) -> None:
    print(f"{timestamp()}:RSS {rss():4,} MB: {msg}")


def __shorten__(path: str, max_lenght: int) -> str:
    if len(path) > max_lenght:
        return path[:3] + "..." + path[(max_lenght - 6) * -1 :]
    else:
        return path


def display_url(clone_url: str, max_length: int = 64) -> str:
    url = re.sub(r"https?://[^\/]+", "", clone_url)  # remove http(s)://host portion of the url
    url = re.sub(r"git@.*:", "", url)  # remove the git@host: portion of the url
    url = __shorten__(url, max_length)
    return re.sub(r".git$", "", url)


def upload_file(source_file: str, destination: str) -> bool:
    with warnings.catch_warnings():
        # google cloud uses deprecated apis
        # suppress the warning locally
        warnings.simplefilter("ignore")
        from google.cloud import storage  # type: ignore [attr-defined] # noqa: E402

    # env variable GOOGLE_APPLICATION_CREDENTIALS must be point to
    # a service account json file
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is None:
        return False

    bucket_name = os.environ.get("GS_BUCKET_NAME", "vinolab")
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination)
        blob.upload_from_filename(source_file)

        stats = os.stat(source_file)
        log(f"uploaded {source_file} to gs://{bucket_name}/{destination}, size {int(stats.st_size/1048576)} MB")
        return True
    except Exception as e:
        print(f"Failed to upload {source_file} to gs://{bucket_name}/{destination}: {e}")
        return False


def normalize_branches(branches: List[str]) -> str:
    """
    normalize list of branch names into a string with comma sperated branches names
    branch names will be shorted by the following logic:
    1. if the branch name contains /, only characters beofre the / will be used
    2. if the branch name is longer than 10 characters, the first 10 characters are used
    the main purpose of this function is to determine is the type of branches a commit is one,
    e.g. main, master, develop, feature, bugfix, etc.
    """
    tmp = {}
    for branch in branches:
        if "->" in branch:
            continue
        branch = re.sub(r"^origin/", "", branch)
        tmp[branch.split("/")[0][:10].strip()] = 1
    keys = list(tmp.keys())
    keys.sort()
    return ",".join(keys)[:1024]


def redact_http_url(url: str) -> str:
    return re.sub(r"(?<=://)[^/]*@", "", url)


def gitlab_ts_to_datetime(ts: None | str) -> None | datetime:
    if ts is None:
        return None
    else:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z")
