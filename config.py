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
    SUPPORTED_SERVICES = ['spotify', 'youtube']
    PYTHONUNBUFFERED = os.environ.get('PYTHONUNBUFFERED')
    TEMPLATES_AUTO_RELOAD = True
    OAUTHLIB_INSECURE_TRANSPORT = os.environ.get('OAUTHLIB_INSECURE_TRANSPORT')

    # used in spotify oauth using the spotipy module
    SPOTIFY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
    SPOTIFY_SCOPES = """ugc-image-upload user-read-recently-played user-read-playback-state
        user-top-read app-remote-control playlist-modify-public user-modify-playback-state
        playlist-modify-private user-follow-modify user-read-currently-playing user-follow-read
        user-library-modify user-read-playback-position playlist-read-private user-read-email
        user-read-private user-library-read playlist-read-collaborative streaming"""

    # used in youtube authorization
    YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')
    YOUTUBE_API_VERSION = 'v3'
    YOUTUBE_CLIENT_SECRETS_FILE = 'yt_client_secrets.json'
    YOUTUBE_SCOPES = [
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.channel-memberships.creator',
        'https://www.googleapis.com/auth/youtube.force-ssl',
        'https://www.googleapis.com/auth/youtube.readonly',
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtubepartner',
        'https://www.googleapis.com/auth/youtubepartner-channel-audit']

    # gets database uri from .env and fallbacks to app.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
