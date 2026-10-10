# Bookmark API

A small REST API for saving links with titles and tags. Built with **Python, FastAPI, and SQLite**, it demonstrates request validation, persistent CRUD operations, pagination, and API tests without needing a database server.

## Quick start

Requires Python 3.11 or newer. Run these commands from the repository directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

On Windows, activate with `.venv\Scripts\activate`. Open http://127.0.0.1:8000/docs for the interactive API explorer.

## Try it

```bash
curl -X POST http://127.0.0.1:8000/bookmarks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Python docs","url":"https://docs.python.org/3/","tag":"python"}'
curl 'http://127.0.0.1:8000/bookmarks?tag=python&limit=10'
```

Example response:

```json
{"id":1,"title":"Python docs","url":"https://docs.python.org/3/","tag":"python","created_at":"2026-10-10T12:00:00.000Z"}
```

IDs and timestamps depend on your database.

## Endpoints

| Method | Route | Behavior |
| --- | --- | --- |
| GET | `/health` | Process health |
| POST | `/bookmarks` | Create a bookmark; duplicate URL returns 409 |
| GET | `/bookmarks` | Newest first; optional exact `tag`, `limit` (1–100), `offset` |
| GET | `/bookmarks/{id}` | Read a bookmark; missing ID returns 404 |
| PUT | `/bookmarks/{id}` | Replace title, URL, and tag |
| DELETE | `/bookmarks/{id}` | Delete a bookmark; returns 204 |

Titles and tags must contain non-whitespace text. URLs accept HTTP/HTTPS and are normalized by Pydantic, so `https://example.com` and `https://example.com/` collide.

## Storage and design

SQLite creates `bookmarks.db` in the current directory on startup. Set `BOOKMARK_DB` to change the path; its parent directory must exist. Each operation uses a separate connection and parameterized SQL. A unique database constraint prevents duplicate URLs, including concurrent inserts. Database files are excluded from Git.

`app.py` contains the application factory, schemas, and routes. `tests/test_api.py` uses isolated temporary databases to exercise CRUD, persistence, duplicate conflicts, filtering, and invalid inputs.

## Run tests

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

GitHub Actions runs the suite on Python 3.11 and 3.14.

## Scope

This is a local learning project with no authentication or multi-user separation. The health route checks the process, not database connectivity. Future extensions could include user accounts, full-text search, and database migrations.

## License

MIT — see [LICENSE](LICENSE).
