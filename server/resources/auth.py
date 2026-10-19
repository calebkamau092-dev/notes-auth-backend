from functools import wraps

from flask import request, session
from flask_restful import Resource
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import User
from schemas import error_list, signup_schema, user_schema


def current_user():
    """The logged-in User, or None."""
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(func):
    """Return 401 unless a user is logged in."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return {"errors": ["You must be logged in."]}, 401
        return func(*args, **kwargs)

    return wrapper


class Signup(Resource):
    def post(self):
        try:
            data = signup_schema.load(request.get_json() or {})
        except ValidationError as err:
            return {"errors": error_list(err.messages)}, 422

        try:
            user = User(username=data["username"])
            user.password_hash = data["password"]
            db.session.add(user)
            db.session.commit()
        except ValueError as err:
            db.session.rollback()
            return {"errors": [str(err)]}, 422
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username is already taken."]}, 422

        session["user_id"] = user.id
        return user_schema.dump(user), 201


class Login(Resource):
    def post(self):
        data = request.get_json() or {}
        user = User.query.filter_by(username=(data.get("username") or "").strip()).first()
        if user is None or not user.authenticate(data.get("password") or ""):
            return {"errors": ["Invalid username or password."]}, 401

        session["user_id"] = user.id
        return user_schema.dump(user), 200


class CheckSession(Resource):
    def get(self):
        user = current_user()
        if user is None:
            # 401 (not 200) so the frontend's `r.ok` check treats this as logged out.
            return {}, 401
        return user_schema.dump(user), 200


class Logout(Resource):
    @login_required
    def delete(self):
        session.pop("user_id", None)
        return {}, 204