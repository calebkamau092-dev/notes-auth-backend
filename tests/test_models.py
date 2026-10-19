import pytest
from sqlalchemy.exc import IntegrityError

from conftest import make_user
from extensions import db
from models import Note, User


def test_password_is_hashed(app):
    user = make_user("alice", "password123")
    assert user._password_hash != "password123"
    assert user._password_hash.startswith("$2b$")


def test_password_hash_cannot_be_read(app):
    user = make_user("alice")
    with pytest.raises(AttributeError):
        user.password_hash


def test_authenticate(app):
    user = make_user("alice", "password123")
    assert user.authenticate("password123")
    assert not user.authenticate("wrong-password")


def test_username_must_be_unique(app):
    make_user("alice")
    with pytest.raises(IntegrityError):
        make_user("alice")


def test_username_length_validation(app):
    with pytest.raises(ValueError):
        User(username="ab")


def test_note_validations(app):
    with pytest.raises(ValueError):
        Note(title="   ", content="Something")
    with pytest.raises(ValueError):
        Note(title="Title", content="")


def test_deleting_user_deletes_their_notes(app):
    user = make_user("alice")
    db.session.add(Note(title="Hi", content="There", user=user))
    db.session.commit()
    db.session.delete(user)
    db.session.commit()
    assert Note.query.count() == 0