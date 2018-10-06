from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    access_token = db.Column(db.String())

    def __init__(self, name, access_token):
        self.name = name
        self.access_token = access_token

    def __repr__(self):
        return '<id {}, name {}>'.format(self.id, self.name)
