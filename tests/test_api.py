from fastapi.testclient import TestClient
import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "test.db")) as client:
        yield client


def payload(url="https://example.com", tag="python"):
    return {"title": "Example", "url": url, "tag": tag}


def test_crud(client):
    response = client.post("/bookmarks", json=payload())
    assert response.status_code == 201
    item = response.json()
    assert item['created_at'].endswith('Z')
    path = f"/bookmarks/{item['id']}"
    assert client.get(path).json()['title'] == 'Example'
    assert client.put(path, json={**payload(), 'title': 'Updated'}).json()['title'] == 'Updated'
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404


def test_duplicates_and_update_conflict(client):
    client.post('/bookmarks', json=payload())
    assert client.post('/bookmarks', json=payload()).status_code == 409
    item = client.post('/bookmarks', json=payload('https://other.example')).json()
    assert client.put(f"/bookmarks/{item['id']}", json=payload()).status_code == 409
    assert client.get(f"/bookmarks/{item['id']}").json()['url'] == 'https://other.example/'


@pytest.mark.parametrize('changes', [{'url': 'file:///tmp/a'}, {'title': ''}, {'title': '  '}, {'tag': ' '}])
def test_validation(client, changes):
    assert client.post('/bookmarks', json={**payload(), **changes}).status_code == 422


def test_filter_and_pagination(client):
    client.post('/bookmarks', json=payload())
    client.post('/bookmarks', json=payload('https://second.example', 'sql'))
    assert len(client.get('/bookmarks?tag=python').json()) == 1
    assert client.get('/bookmarks?limit=1&offset=1').json()[0]['tag'] == 'python'
    assert client.get('/bookmarks?limit=0').status_code == 422
    assert client.get("/bookmarks?tag=' OR 1=1 --").json() == []


def test_missing_mutations(client):
    assert client.delete('/bookmarks/999').status_code == 404
    assert client.put('/bookmarks/999', json=payload()).status_code == 404


def test_persists_across_restarts(tmp_path):
    db = tmp_path / 'persistent.db'
    with TestClient(create_app(db)) as first:
        first.post('/bookmarks', json=payload())
    with TestClient(create_app(db)) as second:
        assert len(second.get('/bookmarks').json()) == 1
