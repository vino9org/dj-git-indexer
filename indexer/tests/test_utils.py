import os

import pytest

from indexer.utils import (
    clone_to_browse_url,
    display_url,
    enumerate_github_repos,
    enumerate_gitlab_repos,
    enumerate_local_repos,
    match_any,
    normalize_branches,
    should_exclude_from_stats,
    upload_file,
)


def test_ignore_patterns():
    # vendered Go dependencies
    assert should_exclude_from_stats("vendor/librar/stuff/blah.go")
    assert should_exclude_from_stats("vendor/librar/stuff/README.md")

    # go module
    assert should_exclude_from_stats("go.sum")

    # binary files
    assert should_exclude_from_stats("lib/my_stupid_jar/blah.jar")
    assert should_exclude_from_stats("java.jar")
    assert should_exclude_from_stats("somepath/logo.png")
    assert should_exclude_from_stats("stuff.pdf")

    # Xcode project
    assert should_exclude_from_stats("Accelerator.xcodeproj/project.pbxproj")

    # Cocoa pod lock
    assert should_exclude_from_stats("Podfile.lock")
    assert should_exclude_from_stats("Pods/Firebase/CoreOnly/Sources/Firebase.h")
    assert should_exclude_from_stats("Something/Pods/Firebase.h")

    # yarn lock
    assert should_exclude_from_stats("yarn.lock")

    # npm lock
    assert should_exclude_from_stats("package-lock.json")
    assert should_exclude_from_stats("someapp/package-lock.json")

    # npm modules
    assert should_exclude_from_stats("node_modules/.app.js")
    assert should_exclude_from_stats("someapp/node_modules/.app.js")

    # Next.js build
    assert should_exclude_from_stats("someapp/.next/_app.js")
    assert should_exclude_from_stats("webretail/.next/static/chunks/pages/_app.js")
    assert should_exclude_from_stats("webretail/.next/static/webpack/pages/indexupdate.js")
    assert should_exclude_from_stats("webretail/.next/server/pages/_document.js")
    assert should_exclude_from_stats("common/assets/Styling/_mixins.scss")

    # IDE/Editor files
    assert should_exclude_from_stats(".vscode/settings.json")
    assert should_exclude_from_stats(".idea/misc.xml")

    # build output
    assert should_exclude_from_stats("target/output/pom.xml")
    assert should_exclude_from_stats("target/output/pom.xml")

    # backkup files
    assert should_exclude_from_stats("src/pom.xml.bak")

    # devcontainer stuff
    assert should_exclude_from_stats(".devcontainer/docker-compose.yml")
    assert should_exclude_from_stats(".devcontainer/local-data/keycloak-data.json")

    assert not should_exclude_from_stats("src/main/my/company/package/Application.java")
    assert not should_exclude_from_stats("src/resources/application.yaml")
    assert not should_exclude_from_stats("Something/another/Pods/Firebase.h")
    assert not should_exclude_from_stats("package.json")
    assert not should_exclude_from_stats("node_modules.txt")
    assert not should_exclude_from_stats(".next.d")

    # not real files but similiar to IDE stuff
    assert not should_exclude_from_stats("idea/misc.xml")
    assert not should_exclude_from_stats("vscode/settings.json")


def test_match_any():
    assert match_any("/Users/lee/tmp/shared/bbx/company/bbx-cookiecutter-springboot3.git", "*/bbx/*/bbx*")
    assert not match_any("/Users/lee/tmp/shared/bbx/cookiecutter-springboot3.git", "*/bbx/bbx*")


def test_clone_to_browse_url():
    assert clone_to_browse_url("https://gitlab.com/someuser/some_repo.git") == "https://gitlab.com/someuser/some_repo"
    assert (
        clone_to_browse_url("git@github.com:sloppycoder/k3s-fluxcd-vinolab.git")
        == "https://github.com/sloppycoder/k3s-fluxcd-vinolab"
    )
    assert clone_to_browse_url("file://base_dir/def/my.git") == ""


def test_enumerate_local_repos(local_repo):
    repos = list(enumerate_local_repos(local_repo))
    assert len(repos) > 0


@pytest.mark.skipif(os.environ.get("GITLAB_TOKEN") is None, reason="gitlab token not available")
def test_enumerate_gitlab_repos(gitlab_test_repo):
    repos = list(enumerate_gitlab_repos(gitlab_test_repo))
    assert len(repos) > 0


def test_enumerate_github_repos(github_test_repo):
    repos = list(enumerate_github_repos(github_test_repo))
    assert len(repos) > 0


def test_display_url():
    assert (
        display_url(
            "https://gitlab.com/securemyphbank/shared/pro/devops/gitlab-ci/shared-gitlab-blueprints/java-ms-blueprint"
        )
        == "/se...evops/gitlab-ci/shared-gitlab-blueprints/java-ms-blueprint"
    )

    assert display_url("https://github.com/sloppy_coder/xyz.git") == "/sloppy_coder/xyz"

    assert (
        display_url("git@gitlab.com:securemyphbank/rtd/pro/local-payment-service-chart.git", 64)
        == "securemyphbank/rtd/pro/local-payment-service-chart"
    )


@pytest.mark.skipif(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") is None, reason="GCP credentials not set")
def test_upload_file():
    assert upload_file(__file__, "test_file.temp")


def test_normalize_branches():
    assert "bugfix,feature,master,release,some_rando" == normalize_branches(
        [
            "origin/feature/presigned-url-generator",
            "origin/feature/debug-error",
            "origin/HEAD -> origin/master",
            "origin/master",
            "release/1.0",
            "bugfix/PROJ-1233",
            "some_random_long_branch_name",
        ]
    )
