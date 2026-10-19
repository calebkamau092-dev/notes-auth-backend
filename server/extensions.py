"""Flask extensions, created here and attached to the app in app.py.

Keeping them in their own module lets models.py and the resources import
them without importing app.py (which would cause a circular import).
"""

from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Naming convention so Alembic migrations get stable constraint names.
metadata = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

db = SQLAlchemy(metadata=metadata)
bcrypt = Bcrypt()
migrate = Migrate()