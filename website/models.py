from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    key = db.Column(db.String(150))
    secret_key = db.Column(db.String(150))
    time_created = db.Column(db.DateTime(timezone=True), default=func.now())
    time_updated = db.Column(db.DateTime(timezone=True), default=func.now())
