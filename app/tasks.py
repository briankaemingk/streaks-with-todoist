import sys
from app.app import create_app
from app.user.models import User
from app.webhooks.todoist_webhook import process_webhook

app = create_app()
app.app_context().push()



def process_webhooks(user_id, req):
    try:
        user = User.query.get(user_id)
        process_webhook(req, user)
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())