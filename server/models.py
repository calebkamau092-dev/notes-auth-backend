from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from extensions import bcrypt, db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=False)

    @hybrid_property
    def password_hash(self):
        """The hash is never readable from outside the model."""
        raise AttributeError("Password hashes may not be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates("username")
    def validate_username(self, key, username):
        username = (username or "").strip()
        if not 3 <= len(username) <= 30:
            raise ValueError("Username must be between 3 and 30 characters.")
        return username

    def __repr__(self):
        return f"<User {self.id} {self.username}>"