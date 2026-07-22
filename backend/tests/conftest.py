# backend/tests/conftest.py
import pytest
import app.db


@pytest.fixture(autouse=True)
def isolate_test_db(monkeypatch, tmp_path):
    """
    Ensure every backend test runs in an isolated temporary SQLite database.
    Prevents tests from mutating any canonical or development database files.
    """
    db_file = str(tmp_path / "test_soulsmith_isolated.db")
    monkeypatch.setenv("SOULSMITH_DB_FILE", db_file)
    app.db.DB_FILE = db_file
    app.db._initialized_files.clear()
    yield
    app.db._initialized_files.clear()
