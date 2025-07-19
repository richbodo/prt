from pathlib import Path
from prt.db import Database


def test_initialize_and_insert_people(tmp_path):
    db_path = tmp_path / "test.db"
    schema_path = Path(__file__).resolve().parents[1] / "docs" / "latest_google_people_schema.json"
    db = Database(db_path)
    db.connect()
    db.initialize(schema_path)

    cur = db.conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='people'")
    assert cur.fetchone() is not None

    people = [
        {
            "resourceName": "people/1",
            "etag": "tag1",
            "names": [{"displayName": "Alice Example"}],
            "emailAddresses": [{"value": "alice@example.com"}],
        },
        {
            "resourceName": "people/2",
            "etag": "tag2",
            "names": [{"displayName": "Bob Example"}],
            "emailAddresses": [{"value": "bob@example.com"}],
        },
        {
            "resourceName": "people/3",
            "etag": "tag3",
            "names": [{"displayName": "Carol Example"}],
            "emailAddresses": [{"value": "carol@example.com"}],
        },
    ]
    db.insert_people(people)

    cur.execute("SELECT resourceName FROM people ORDER BY resourceName")
    rows = [r[0] for r in cur.fetchall()]
    assert rows == ["people/1", "people/2", "people/3"]
