import sqlalchemy


def test_create_app_with_non_sqlite_url(monkeypatch):
    from habittracker import app as app_module
    from habittracker import database

    captured = {}
    original_create_engine = sqlalchemy.create_engine
    original_engine = database.engine

    def fake_create_engine(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return original_create_engine("sqlite:///:memory:")

    monkeypatch.setattr(app_module, "create_engine", fake_create_engine)

    class _DummyEngine:
        def dispose(self):
            pass

    database.engine = _DummyEngine()

    non_sqlite_url = "postgresql://user:pass@localhost:5432/habittracker"

    try:
        app = app_module.create_app(non_sqlite_url)

        assert app is not None
        assert captured["url"] == non_sqlite_url
        assert "connect_args" not in captured["kwargs"]
    finally:
        database.engine.dispose()
        database.engine = original_engine
        database.SessionLocal.configure(bind=original_engine)
