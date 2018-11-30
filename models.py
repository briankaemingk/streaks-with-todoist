from app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String())
    jit_feature = db.Column(db.Boolean())
    recurrence_resch_feature = db.Column(db.Boolean())
    streaks_feature = db.Column(db.Boolean())

    def __init__(self, id, access_token):
        self.id = id
        self.access_token = access_token
        self.jit_feature = True
        self.recurrence_resch_feature = True
        self.streaks_feature = True

    def __repr__(self):
        return '<id {}, access token {}>'.format(self.id, self.access_token)
