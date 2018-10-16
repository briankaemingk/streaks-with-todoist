from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String())

    def __init__(self, id, access_token):
        self.id = id
        self.access_token = access_token

    def __repr__(self):
        return '<id {}, access token {}>'.format(self.id, self.access_token)
