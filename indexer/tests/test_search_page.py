# please see conftest.py for seed data


from urllib.parse import urlencode


def test_search_by_hash(client, db):
    sha = "feb3a2837630c0e51447fc1d7e68d86f964a8440"
    response = client.get(f"/indexer/search?query={sha}")
    assert response.status_code == 200
    assert bytes(sha, "utf-8") in response.content


def test_search_by_email(client, db):
    query = {"query": "mini@me"}
    response = client.get(f"/indexer/search?{urlencode(query)}")
    assert response.status_code == 200
    assert b"e2c8b79813b95c93e5b06c5a82e4c417d5020762" in response.content


def test_search_by_repo_name(client, db):
    response = client.get("/indexer/search?query=repo")
    assert response.status_code == 200
    assert b"ee474544052762d314756bb7439d6dab73221d3d" in response.content


def test_search_by_bad_hash(client, db):
    sha = "feb3a2837630c0e51447fc1d7e68d86f964a8442"
    response = client.get(f"/indexer/search?query={sha}")
    assert response.status_code == 200
    assert b"cannot find commit" in response.content
