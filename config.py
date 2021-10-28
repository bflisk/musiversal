import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

if basedir[-1] == '/':
    load_dotenv(os.path.join(basedir, '.env')) # running on windows
else:
    load_dotenv(os.path.join(basedir, '/.env')) # running on mac

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_NAME = 'musiversal cookie'
    PYTHONUNBUFFERED = os.environ.get('PYTHONUNBUFFERED')

    # used in spotify oauth using the spotipy module
    SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')

    # gets database uri from .env and fallbacks to app.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TEMPLATES_AUTO_RELOAD = True

    #SUPPORTED_SERVICES = ['spotify', 'soundcloud', 'youtube']
