import spotipy.util as util

from os import environ
from time import time
from flask import session
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

class spotify():
    SPOTIPY_CLIENT_ID = environ.get('SPOTIPY_CLIENT_ID')
    SPOTIPY_CLIENT_SECRET = environ.get('SPOTIPY_CLIENT_SECRET')

    # creates a spotify authorization object
    def auth(self):
        return SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=url_for('main.index',_external=True),
            scope="""ugc-image-upload user-read-recently-played user-read-playback-state
            user-top-read app-remote-control playlist-modify-public user-modify-playback-state
            playlist-modify-private user-follow-modify user-read-currently-playing user-follow-read
            user-library-modify user-read-playback-position playlist-read-private user-read-email
            user-read-private user-library-read playlist-read-collaborative streaming""")

    # returns a valid access token, refreshing it if needed
    def get_token(self):
        token_info = session.get("token_info", None) # Gives token information if it exists, otherwise given 'None'

        # redirects user to login if token_info is 'None'
        if not token_info:
            return redirect(url_for("main.login", _external=True))

        # checks if token is close to expiring
        now = int(time()) # Gets current time
        is_expired = (token_info['expires_at'] - now) < 60 # T or F depending on condition

        # if the token is close to expiring, refresh it
        if is_expired:
            sp_oauth = self.auth()
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])

        session['token_info'] = token_info

        return token_info

    # creates a spotify object
    def create_sp(self):
        # tries to get token data. If it doesn't succeed, returns false
        try:
            token_info = self.get_token()
            sp = spotipy.Spotify(auth=token_info['access_token'])
        except:
            return False

        return sp
