from flask import Flask
from rq import Queue
from worker import conn
from app import public, user
from app.extensions import db

def create_app(config_object='app.settings'):
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    register_extensions(app)
    register_blueprints(app)
    return app


def register_extensions(app):
    db.init_app(app)
    return None

def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(public.views.blueprint)
    return None


q = Queue(connection=conn)

