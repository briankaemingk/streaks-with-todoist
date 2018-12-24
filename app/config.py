import os
basedir = os.path.abspath(os.path.dirname(__file__))
from environs import Env
env = Env()
env.read_env()


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    ENV = env.str('FLASK_ENV', default='production')
    DEBUG = ENV == 'development'
    SQLALCHEMY_DATABASE_URI = env.str('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CLIENT_SECRET = env.str('CLIENT_SECRET')
    CLIENT_ID = env.str('CLIENT_ID')
    REDIS_URL = env.str('REDIS_URL')
    SECRET_KEY = env.str('SECRET_KEY')

class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True