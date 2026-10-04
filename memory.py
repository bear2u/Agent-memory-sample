"""A small persistent memory store. Python 3.9+, standard library only."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path


class MemoryStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS memories (
                user_id TEXT NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                written_by TEXT NOT NULL,
                PRIMARY KEY (user_id, topic)
            )''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, user_id, topic, content, written_by):
        if not all(str(value).strip() for value in (user_id, topic, content)):
            raise ValueError("사용자, 주제, 기억 내용은 비어 있을 수 없습니다.")
        with self.connect() as db:
            db.execute('''INSERT INTO memories VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, topic) DO UPDATE SET
                content = excluded.content, written_by = excluded.written_by''',
                (user_id, topic, content, written_by))

    def read(self, user_id, topic):
        with self.connect() as db:
            row = db.execute(
                'SELECT content FROM memories WHERE user_id = ? AND topic = ?',
                (user_id, topic)).fetchone()
        return row[0] if row else None

    def search(self, user_id, keyword):
        # Literal substring search, NOT semantic/vector search.
        return [row for row in self.list_for(user_id) if keyword in row['content']]

    def list_for(self, user_id):
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute('''SELECT user_id, topic, content, written_by
                FROM memories WHERE user_id = ? ORDER BY topic''', (user_id,)).fetchall()
        return [dict(row) for row in rows]

    def delete(self, user_id, topic):
        with self.connect() as db:
            result = db.execute(
                'DELETE FROM memories WHERE user_id = ? AND topic = ?',
                (user_id, topic))
        return result.rowcount > 0
