# please see conftest.py for seed data


def test_search_by_hash(client, db):
    sha = "feb3a2837630c0e51447fc1d7e68d86f964a8440"
    response = client.post("/indexer/", {"query": sha}, follow=True)
    assert response.status_code == 200
    assert bytes(sha, "utf-8") in response.content


def test_search_by_email(client, db):
    response = client.post("/indexer/", {"query": "mini@me"}, follow=True)
    assert response.status_code == 200
    assert b"e2c8b79813b95c93e5b06c5a82e4c417d5020762" in response.content


def test_search_by_repo_name(client, db):
    response = client.post("/indexer/", {"query": "repo"}, follow=True)
    assert response.status_code == 200
    assert b"ee474544052762d314756bb7439d6dab73221d3d" in response.content


def test_search_by_bad_hash(client, db):
    sha = "feb3a2837630c0e51447fc1d7e68d86f964a8442"
    response = client.post("/indexer/", {"query": sha}, follow=True)
    assert response.status_code == 200
    assert b"cannot find commit" in response.content
