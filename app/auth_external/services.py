import spotipy.util as util
import spotipy

from config import Config
from time import time
from flask import session, url_for, redirect
from flask_login import current_user
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

class Soundcloud():
    def auth(self):
        return 1

class Spotify():
    # creates a spotify authorization object
    def create_oauth(self):
        return SpotifyOAuth(
            client_id=Config.SPOTIPY_CLIENT_ID,
            client_secret=Config.SPOTIPY_CLIENT_SECRET,
            redirect_uri=url_for('auth_external.auth_redirect', _external=True, service='spotify'),
            scope="""ugc-image-upload user-read-recently-played user-read-playback-state
            user-top-read app-remote-control playlist-modify-public user-modify-playback-state
            playlist-modify-private user-follow-modify user-read-currently-playing user-follow-read
            user-library-modify user-read-playback-position playlist-read-private user-read-email
            user-read-private user-library-read playlist-read-collaborative streaming""")

    # returns a valid access token, refreshing it if needed
    def get_token(self):
        token_info = session.get("sp_token_info", None) # Gives token information if it exists, otherwise given 'None'

        # redirects user to login if token_info is 'None'
        if not token_info:
            return redirect(url_for("main.index", _external=True))

        # checks if token is close to expiring
        now = int(time()) # Gets current time
        is_expired = (token_info['expires_at'] - now) < 60 # T or F depending on condition

        # if the token is close to expiring, refresh it
        if is_expired:
            sp_oauth = self.create_oauth()
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])

        session['token_info'] = token_info

        return token_info

    # creates a spotify object
    def create_sp(self):
        # tries to get token data. If it doesn't succeed, returns false
        #try:
        token_info = self.get_token()
        sp = spotipy.Spotify(auth=token_info['access_token'])
        #except:
        #    return False

        return sp

class Youtube():
    def auth(self):
        return 1
