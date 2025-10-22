import sqlite3
from typing import List, Dict, Any
from datetime import datetime

DB_PATH = 'tasks.db'

CREATE_SQL = '''
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT,
    price REAL DEFAULT 0.0,
    level INTEGER DEFAULT 0,
    done INTEGER DEFAULT 0,
    created_at TEXT
);
'''

class TasksDB:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._ensure_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _ensure_db(self):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(CREATE_SQL)
            conn.commit()
        finally:
            conn.close()

    def add_task(self, title: str, category: str, price: float, level: int, done: int) -> int:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO tasks (title, category, price, level, done, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                (title, category, price, level, int(done), datetime.utcnow().isoformat())
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def update_task(self, task_id: int, **kwargs):
        if not kwargs:
            return
        keys = []
        values = []
        for k, v in kwargs.items():
            keys.append(f"{k} = ?")
            values.append(v)
        values.append(task_id)
        sql = f"UPDATE tasks SET {', '.join(keys)} WHERE id = ?"
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, values)
            conn.commit()
        finally:
            conn.close()

    def delete_task(self, task_id: int):
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
        finally:
            conn.close()

    def list_tasks(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute('SELECT id, title, category, price, level, done, created_at FROM tasks ORDER BY id DESC')
            rows = cur.fetchall()
            tasks = []
            for r in rows:
                tasks.append({
                    'id': r[0],
                    'title': r[1],
                    'category': r[2],
                    'price': r[3],
                    'level': r[4],
                    'done': int(r[5]),
                    'created_at': r[6]
                })
            return tasks
        finally:
            conn.close()
