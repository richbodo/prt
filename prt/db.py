import sqlite3
import shutil
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any


class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.conn = None

    def connect(self) -> None:
        self.conn = sqlite3.connect(self.path)

    def is_valid(self) -> bool:
        """Check if the database is valid using SQLite integrity check."""
        if self.conn is None:
            return False
        try:
            cur = self.conn.cursor()
            cur.execute("PRAGMA integrity_check")
            return cur.fetchone()[0] == "ok"
        except sqlite3.DatabaseError:
            return False

    def initialize(self, schema_path: Path) -> None:
        """Initialize database tables using the provided Google People schema."""
        cur = self.conn.cursor()
        if schema_path:
            with open(schema_path, "r") as f:
                schema = json.load(f)
            columns = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]
            for prop in schema.get("properties", {}).keys():
                columns.append(f'"{prop}" TEXT')
            cur.execute(f'CREATE TABLE IF NOT EXISTS people ({", ".join(columns)})')

        cur.execute(
            'CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY, name TEXT, email TEXT)'
        )
        cur.execute(
            'CREATE TABLE IF NOT EXISTS relationships (id INTEGER PRIMARY KEY, contact_id INTEGER, tag TEXT, note TEXT)'
        )
        self.conn.commit()

    def backup(self, suffix: str = ".bak") -> Path:
        """Backup the database file with a custom suffix.

        Parameters
        ----------
        suffix: str
            Suffix to append to the database filename. Defaults to ".bak".

        Returns
        -------
        Path
            Path to the backup file.
        """
        backup_path = self.path.with_name(self.path.name + suffix)
        if self.path.exists():
            shutil.copy(self.path, backup_path)
        return backup_path

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

    def insert_people(self, people: List[Dict[str, Any]]):
        """Insert list of people dictionaries into the people table."""
        cur = self.conn.cursor()
        for person in people:
            columns = []
            values = []
            for k, v in person.items():
                columns.append(f'"{k}"')
                if isinstance(v, (dict, list)):
                    values.append(json.dumps(v))
                else:
                    values.append(v)
            placeholders = ",".join(["?"] * len(values))
            cur.execute(
                f'INSERT INTO people({", ".join(columns)}) VALUES ({placeholders})',
                values,
            )
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
