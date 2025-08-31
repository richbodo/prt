from sqlalchemy import text

from prt_src.api import PRTAPI


def _make_api(test_db):
    db, _ = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    return PRTAPI(config)


def test_execute_sql_read_only_returns_rows(test_db):
    api = _make_api(test_db)
    result = api.execute_sql("SELECT name FROM contacts ORDER BY id LIMIT 1")
    assert result["error"] is None
    assert isinstance(result["rows"], list)
    assert result["rowcount"] == 1


def test_execute_sql_write_requires_confirmation(test_db):
    api = _make_api(test_db)
    initial = api.db.session.execute(text("SELECT COUNT(*) FROM contacts")).scalar()
    result = api.execute_sql("DELETE FROM contacts WHERE id=1")
    assert result["error"] is not None
    assert "confirm" in result["error"].lower()
    count = api.db.session.execute(text("SELECT COUNT(*) FROM contacts")).scalar()
    assert count == initial


def test_execute_sql_backup_before_write(test_db, monkeypatch):
    api = _make_api(test_db)
    called = {}

    def fake_backup(op):
        called["op"] = op
        return {}

    monkeypatch.setattr(api, "auto_backup_before_operation", fake_backup)
    result = api.execute_sql("UPDATE contacts SET name='Changed' WHERE id=1", confirm=True)
    assert called
    assert result["rowcount"] == 1
    name = api.db.session.execute(text("SELECT name FROM contacts WHERE id=1")).scalar()
    assert name == "Changed"
