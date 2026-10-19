import pytest

from app import create_app
from extensions import db
from models import Note, User


@pytest.fixture
def app():
    """A fresh app with an in-memory database for every test."""
    app = create_app("sqlite://")
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client. It keeps the session cookie between requests, like a browser."""
    return app.test_client()


def make_user(username, password="password123"):
    user = User(username=username)
    user.password_hash = password
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def alice(app):
    return make_user("alice")


@pytest.fixture
def bob(app):
    return make_user("bob")


@pytest.fixture
def logged_in_client(client, alice):
    client.post("/login", json={"username": "alice", "password": "password123"})
    return client


@pytest.fixture
def bobs_note(bob):
    note = Note(title="Bob's secret", content="Only Bob can see this.", user=bob)
    db.session.add(note)
    db.session.commit()
    return note