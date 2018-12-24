from app.extensions import db
from flask import current_app
import redis
import rq

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    access_token = db.Column(db.String())
    jit_feature = db.Column(db.Boolean())
    recurrence_resch_feature = db.Column(db.Boolean())
    streaks_feature = db.Column(db.Boolean())
    in_line_comment_feature = db.Column(db.Boolean())

    def __init__(self, id, access_token, jit_feature, recurrence_resch_feature, streaks_feature, in_line_comment_feature):
        self.id = id
        self.access_token = access_token
        self.jit_feature = jit_feature
        self.recurrence_resch_feature = recurrence_resch_feature
        self.streaks_feature = streaks_feature
        self.in_line_comment_feature = in_line_comment_feature

    def __repr__(self):
        return '<id {}, access token {}>'.format(self.id, self.access_token)

    def launch_task(self, name, description, *args, **kwargs):
        current_app.task_queue.enqueue('app.tasks.' + name, self.id, *args, **kwargs)





