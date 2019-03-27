from flask import Flask
from app import public, user, auth, webhooks
from app.config import Config
from app.extensions import db, migrate
from redis import Redis
import rq
import atexit

from apscheduler.schedulers.background import BackgroundScheduler


def print_date_time():
    print('Timer run')

scheduler = BackgroundScheduler()
scheduler.add_job(func=print_date_time, trigger="cron", minute=30)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


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