from flask import Flask
from app import public, user
from app.config import Config
from app.extensions import db, migrate
from redis import Redis
import rq

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
    app.register_blueprint(public.views.blueprint)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'User': user.models.User,
            'Task': user.models.Task}

    app.shell_context_processor(shell_context)