import os

from flask import Flask
from flask_restful import Api

from extensions import bcrypt, db, migrate
from resources.auth import CheckSession, Login, Logout, Signup


def create_app(database_uri="sqlite:///app.db"):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Signs the session cookie. Set SECRET_KEY in the environment outside development.
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    api = Api(app)
    api.add_resource(Signup, "/signup")
    api.add_resource(Login, "/login")
    api.add_resource(CheckSession, "/check_session")
    api.add_resource(Logout, "/logout")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(port=5555, debug=True)