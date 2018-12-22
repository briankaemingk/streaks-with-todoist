import os
from app.utils import initiate_api
from app.app import app, db

app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from app.user.models import User


user_list = User.query.order_by(User.id).all()

for user in user_list:
    api = initiate_api(user.access_token)
    user.streaks_feature = True

    if api.state['user']['is_premium']:
        user.recurrence_resch_feature = True
        user.jit_feature = True
        user.in_line_comment_feature = True
        db.session.commit()
    else:
        user.recurrence_resch_feature = False
        user.jit_feature = False
        user.in_line_comment_feature = False
        db.session.commit()

