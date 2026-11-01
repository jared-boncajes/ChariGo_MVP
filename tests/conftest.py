import pytest
from app import create_app
from models import db
from seed import seed_database


@pytest.fixture
def app(tmp_path):
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-session-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.db"),
            "UPLOAD_FOLDER": str(tmp_path / "images"),
            "PRIVATE_FOLDER": str(tmp_path / "portfolios"),
        }
    )
    with app.app_context():
        db.create_all()
        seed_database()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, url, data=None, **kwargs):
    client.get("/login")
    with client.session_transaction() as session:
        token = session["csrf_token"]
    return client.post(url, data={"csrf_token": token, **(data or {})}, **kwargs)


def login(client, email="goer@example.com"):
    return post(
        client,
        "/login",
        {"email": email, "password": "ChariGo123!"},
        follow_redirects=True,
    )
