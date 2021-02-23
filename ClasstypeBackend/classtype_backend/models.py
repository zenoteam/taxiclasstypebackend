from datetime import datetime

from sqlalchemy import func
from classtype_backend.db import db


class ClasstypeModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_name = db.Column(db.String)
    class_description = db.Column(db.String)
    updateTimestamp = db.Column(db.DateTime, onupdate=datetime.now)
    timestamp = db.Column(db.DateTime, server_default=func.now())
