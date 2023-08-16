from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy  #useful to handle databases

db = SQLAlchemy()

class UserModel(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer(), primary_key=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow())
    username = db.Column(db.String(), nullable=False)
    # Use Right email and password data types instead of strings
    email = db.Column(db.String(), nullable=False, unique=True)
    password = db.Column(db.String(), nullable=False)

    def __init__(self, data) -> None:
        self.username = data['username']
        self.email = data['email']
        self.password = data['password']

    def __repr__(self) -> str:
        return "USER DETAILS: {'ID' : {}, 'Username' : {}, 'Email' : {}, 'Password' : {}, 'Created At' : {}}".format(self.id, self.username, self.email, self.password, self.created_at)
