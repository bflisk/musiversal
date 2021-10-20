import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # gets database uri from .env and fallbacks to app.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
