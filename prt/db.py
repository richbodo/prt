import sqlite3
import shutil
from pathlib import Path
from typing import List, Tuple


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.conn = None

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.path)

    def initialize(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, name TEXT, email TEXT)'
        )
        cur.execute(
            'CREATE TABLE IF NOT EXISTS relationships (id INTEGER PRIMARY KEY, contact_id INTEGER, tag TEXT, note TEXT)'
        )
        self.conn.commit()

    def backup(self) -> None:
        backup_path = self.path.with_suffix('.bak')
        if self.path.exists():
            shutil.copy(self.path, backup_path)

    def count_contacts(self) -> int:
        cur = self.conn.cursor()
        cur.execute('SELECT COUNT(*) FROM contacts')
        return cur.fetchone()[0]

    def count_relationships(self) -> int:
        cur = self.conn.cursor()
        cur.execute('SELECT COUNT(*) FROM relationships')
        return cur.fetchone()[0]

    def insert_contacts(self, contacts: List[Tuple[str, str]]):
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO contacts(name, email) VALUES (?, ?)', contacts)
        self.conn.commit()

    def list_contacts(self) -> List[Tuple[int, str, str]]:
        cur = self.conn.cursor()
        cur.execute('SELECT id, name, email FROM contacts ORDER BY name')
        return cur.fetchall()

    def add_relationship(self, contact_id: int, tag: str, note: str):
        cur = self.conn.cursor()
        cur.execute(
            'INSERT INTO relationships(contact_id, tag, note) VALUES (?, ?, ?)',
            (contact_id, tag, note),
        )
        self.conn.commit()
