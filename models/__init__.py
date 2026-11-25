from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .event import Event
from .registration import Registration

__all__ = ["db", "User", "Event", "Registration"]
