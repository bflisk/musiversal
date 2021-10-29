from config import Config
from time import time
from flask import session, url_for, redirect
from flask_login import current_user

import spotipy.util as util
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from googleapiclient.discovery import build

class Soundcloud():
    def auth(self):
        return 1

# handles the authorization and interfacing with the spotify api
class Spotify():
    oauth = None # used to authorize with spotify
    api = None # used to interface with spotify api

    # creates a spotify authorization object
    def __init__(self):
        self.oauth =  SpotifyOAuth(
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
        if type(token_info) != dict:
            return redirect(url_for('main.index', _external=True))

        # checks if token is close to expiring
        now = int(time())
        is_expired = (token_info['expires_at'] - now) < 60

        # if the token is close to expiring, refresh it
        if is_expired:
            token_info = self.oauth.refresh_access_token(token_info['refresh_token'])

        session['token_info'] = token_info

        return token_info

    # creates api object and passes it into itself
    def create_api(self):
        # tries to get token data
        try:
            token_info = self.get_token()
            sp = spotipy.Spotify(auth=token_info['access_token'])
        except:
            sp = None

        self.api = sp

    # returns search results
    def search(self, query):
        # SEARCH FOR QUERY HERE #
        return results

# handles the authorization and interfacing with the youtube api
class Youtube():
    api = None # used to interface with the youtube api

    # authorizes the user with youtube
    def __init__(self):
        self.api = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)

    def statistics(self, channel_id):
        # 'UCRF5G3zVPHuuMiPPd84SG7Q'
        request = self.api.channels().list(part='statistics', id=channel_id)
        response = request.execute()

        return response

    # returns search results for a given query
    def search(self, query):
        request = self.api.search().list(part='snippet', q=query)
        response = request.execute()

        return response
