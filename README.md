# Bookmark API

Save links with a title and one tag, then fetch, update, or delete them. Uses FastAPI and a local SQLite file.

## Run locally

Python 3.11+. From this folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

On Windows, activate with `.venv\Scripts\activate`. Open [localhost:8000/docs](http://127.0.0.1:8000/docs) to try the routes.

```sh
curl -X POST http://127.0.0.1:8000/bookmarks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Python docs","url":"https://docs.python.org/3/","tag":"python"}'
curl 'http://127.0.0.1:8000/bookmarks?tag=python&limit=10'
```

`GET /bookmarks` lists newest first, with optional `tag`, `limit` (1–100), and `offset`. Use `/bookmarks/{id}` with GET, PUT, or DELETE for one entry. PUT replaces all fields; an omitted tag becomes `general`.

## A few details

`app.py` holds the schemas, routes, and queries. Each request opens its own connection. URLs must use HTTP/HTTPS; normalized duplicates return 409. A missing ID returns 404. Tag filters match exactly, including case.

The default file is `bookmarks.db`. Set `BOOKMARK_DB` to another path in an existing directory. There are no accounts or authentication, so keep this local. `/health` doesn't check the database.

Tests use temporary databases:

```sh
pip install -r requirements-dev.txt
python -m pytest -q
```

[MIT](LICENSE)
