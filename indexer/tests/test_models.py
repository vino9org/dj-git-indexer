from indexer.models import Author, Commit, Repository


def test_query_models(db):
    author = Author.objects.get(name="me")
    assert author.id is not None
    assert len(author.commits.all()) == 3

    commit = Commit.objects.get(sha="feb3a2837630c0e51447fc1d7e68d86f964a8440")
    assert commit is not None
    assert commit.author_id == author.id
    assert len(commit.files.all()) == 3

    # test commit to repo many-to-many relation
    repos = commit.repos.all()
    assert len(repos) == 2
    assert repos[0].clone_url == "https://github.com/super/repo.git"

    commit2 = Commit.objects.get(sha="ee474544052762d314756bb7439d6dab73221d3d")
    assert commit2 is not None and len(commit2.repos.all()) == 1

    # test repo to commit many-to-many relation
    repo = Repository.objects.get(clone_url="https://github.com/super/repo.git")
    assert repo is not None
    assert len(repo.commits.all()) == 2

    # test repo to merge request one-to-many relation
    requests = repo.merge_requests.all()
    assert len(requests) == 2
    assert requests[0].request_id == "MR1"
