from flask import Flask
from todoist.api import TodoistAPI
from app import public, user, auth, webhooks
from app.user.models import User
from app.webhooks.todoist_webhook import get_now_user_timezone
from app.config import Config
from app.extensions import db, migrate
from redis import Redis
import rq
import atexit

from apscheduler.schedulers.background import BackgroundScheduler


def create_app(config_class=Config):
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_class)
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('swt-tasks', connection=app.redis)
    register_extensions(app)
    register_shellcontext(app)
    register_blueprints(app)
    return app


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.routes.blueprint)
    app.register_blueprint(auth.routes.blueprint, url_prefix='/auth')
    app.register_blueprint(webhooks.routes.blueprint, url_prefix='/webhooks')
    app.register_blueprint(user.routes.blueprint, url_prefix='/user')
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User}

    app.shell_context_processor(shell_context)

def hourly():

    app = create_app()
    app.app_context().push()

    print('Timer run')
    users = User.query.all()

    for user in users:
        api = TodoistAPI(user.access_token)
        now = get_now_user_timezone(api)
        print(now.hour, '   ', api.state['items'])

        if(now.hour == 0):
            tasks = api.state['items']
    # for task in tasks:
    #     due_date_utc = task["due_date_utc"]
    #     if due_date_utc:
    #         due_date = convert_time_str_datetime(due_date_utc, user_timezone)
    #         # If the task is due yesterday and it is a habit
    #         if is_habit(task['content']) and is_due_yesterday(due_date, now):
    #             update_streak(task, 0)
    #             task.update(due_date_utc=update_to_all_day(now))
    #             task.update(date_string=task['date_string'] + ' starting tod')
    #             print(task['date_string'])
    #             api.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=hourly, trigger="cron", minute=29)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

