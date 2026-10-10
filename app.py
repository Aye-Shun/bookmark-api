"""A small persistent bookmark API. Run with uvicorn app:app --reload."""
from contextlib import asynccontextmanager, contextmanager
import os
from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field, HttpUrl


class BookmarkInput(BaseModel):
    title: str = Field(min_length=1, max_length=200, pattern=r"\S")
    url: HttpUrl
    tag: str = Field(default="general", min_length=1, max_length=40, pattern=r"\S")


class Bookmark(BookmarkInput):
    id: int
    created_at: str


def create_app(database: str | Path = "bookmarks.db") -> FastAPI:
    # Each request gets its own connection; SQLite enforces URL uniqueness.
    @contextmanager
    def connection():
        db = sqlite3.connect(str(database), timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @asynccontextmanager
    async def lifespan(app):
        with connection() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                tag TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            )""")
        yield

    app = FastAPI(title="Bookmark API", version="1.0.0", lifespan=lifespan)

    def find(db, bookmark_id):
        row = db.execute("SELECT * FROM bookmarks WHERE id = ?", (bookmark_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Bookmark not found")
        return dict(row)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/bookmarks", response_model=Bookmark, status_code=201)
    def create(bookmark: BookmarkInput):
        try:
            with connection() as db:
                cursor = db.execute(
                    "INSERT INTO bookmarks (title, url, tag) VALUES (?, ?, ?)",
                    (bookmark.title.strip(), str(bookmark.url), bookmark.tag.strip()),
                )
                return find(db, cursor.lastrowid)
        except sqlite3.IntegrityError:
            raise HTTPException(409, "URL already saved") from None

    @app.get("/bookmarks", response_model=list[Bookmark])
    def list_bookmarks(tag: str | None = None, limit: int = Query(50, ge=1, le=100),
                       offset: int = Query(0, ge=0)):
        with connection() as db:
            if tag is None:
                rows = db.execute("SELECT * FROM bookmarks ORDER BY id DESC LIMIT ? OFFSET ?",
                                  (limit, offset))
            else:
                rows = db.execute("SELECT * FROM bookmarks WHERE tag = ? ORDER BY id DESC LIMIT ? OFFSET ?",
                                  (tag, limit, offset))
            return [dict(row) for row in rows]

    @app.get("/bookmarks/{bookmark_id}", response_model=Bookmark)
    def get(bookmark_id: int):
        with connection() as db:
            return find(db, bookmark_id)

    @app.put("/bookmarks/{bookmark_id}", response_model=Bookmark)
    def update(bookmark_id: int, bookmark: BookmarkInput):
        try:
            with connection() as db:
                find(db, bookmark_id)
                db.execute("UPDATE bookmarks SET title = ?, url = ?, tag = ? WHERE id = ?",
                           (bookmark.title.strip(), str(bookmark.url), bookmark.tag.strip(), bookmark_id))
                return find(db, bookmark_id)
        except sqlite3.IntegrityError:
            raise HTTPException(409, "URL already saved") from None

    @app.delete("/bookmarks/{bookmark_id}", status_code=204)
    def delete(bookmark_id: int):
        with connection() as db:
            find(db, bookmark_id)
            db.execute("DELETE FROM bookmarks WHERE id = ?", (bookmark_id,))
        return Response(status_code=204)

    return app


app = create_app(os.environ.get("BOOKMARK_DB", "bookmarks.db"))
