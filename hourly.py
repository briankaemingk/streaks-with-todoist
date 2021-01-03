from flask import Flask
from app.user.models import User
from app.extensions import db, migrate
from app.config import Config
from redis import Redis
import rq
from app import public, user, auth, webhooks
from app.webhooks.todoist_webhook import get_now_user_timezone, initiate_api, convert_time_str_datetime, is_habit, update_streak, is_due_yesterday, update_to_all_day, get_user_timezone

def hourly(app):

    app.app_context().push()

    print('Timer run')
    users = User.query.all()

    for user in users:
        api = initiate_api(user.access_token)
        if api is None:
            return 'Request for Streaks with Todoist not authorized, exiting.'
        else:
            now = get_now_user_timezone(api)
            tomorrow = now + timedelta(days=1)
            user_timezone = get_user_timezone(api)
            print("User timezone: ", user_timezone, " Hour: ", now.hour)

            if(now.hour == 0):
                print("Running at midnight local time")
                tasks = api.state['items']
                user_timezone = get_user_timezone(api)

                for task in tasks:
                    if task['is_deleted'] == 0:
                        try:
                            if task['checked'] == 0:
                                if task['due']:
                                    if task['content'].startswith("Cleared L2"):
                                        print('Updating Cleared L2 task')
                                        task.update(due=eval('{' + update_to_all_day(tomorrow) + ', "string" : "ev! other day" }'))
                                    else:
                                        due_date = task['due']['date'][:10] if len(task['due']['date']) > 10 else task['due']['date']
                                        # If the task is due yesterday and it is a habit
                                        print("Checking task: " + task['content'])
                                        if is_habit(task['content']) and is_due_yesterday(due_date, now):
                                            print('Updating overdue for task: ', task['content'])
                                            update_streak(task, 0)
                                            task.update(due=eval('{' + update_to_all_day(now) + ', "string" : "' + task['due']['string'] + '" }'))
                                            print("Updated to new date: ", task['due'])
                        except KeyError: print('KEY ERROR')
            api.commit()
    db.session.remove()

def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    return None

def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User}
    app.shell_context_processor(shell_context)

def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.routes.blueprint)
    app.register_blueprint(auth.routes.blueprint, url_prefix='/auth')
    app.register_blueprint(webhooks.routes.blueprint, url_prefix='/webhooks')
    app.register_blueprint(user.routes.blueprint, url_prefix='/user')
    return None

config_class=Config
app = Flask(__name__.split('.')[0])
# app.config.from_object(config_class)
# app.redis = Redis.from_url(app.config['REDIS_URL'])
# app.task_queue = rq.Queue('swt-tasks', connection=app.redis)
# register_extensions(app)
# register_shellcontext(app)
# register_blueprints(app)

hourly(app)


