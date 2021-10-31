from config import Config
from time import time
from flask import session, url_for, redirect, request
from flask_login import current_user
#from app.models import Service

import spotipy.util as util
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class Soundcloud():
    def auth(self):
        return 1

# handles the authorization and interfacing with the spotify api
class Spotify():

    # initialized with a spotify authorization object
    def __init__(self):
        self.oauth =  SpotifyOAuth(
            client_id=Config.SPOTIFY_CLIENT_ID,
            client_secret=Config.SPOTIFY_CLIENT_SECRET,
            redirect_uri=url_for('auth_external.auth_redirect', _external=True, service='spotify'),
            scope=Config.SPOTIFY_SCOPES)

        self.auth_url = self.oauth.get_authorize_url() # used to redirect spotify to auth_redirect

    # returns a valid access token, refreshing it if needed
    def get_token(self):
        token_info = session.get('sp_token_info', None) # Gives token information if it exists, otherwise given 'None'

        # redirects user to login if token_info is 'None'
        if type(token_info) != dict:
            return redirect(url_for('main.index', _external=True))

        # checks if token is close to expiring
        now = int(time())
        is_expired = (token_info['expires_at'] - now) < 60

        # if the token is close to expiring, refresh it
        if is_expired:
            token_info = self.oauth.refresh_access_token(token_info['refresh_token'])

        session['sp_token_info'] = token_info

        return token_info

    # creates api object and passes it into itself
    def create_api(self):
        # tries to get token data
        try:
            token_info = self.get_token()
            self.api = spotipy.Spotify(auth=token_info['access_token'])
        except:
            self.api = None

    # returns search results
    def search(self, query):
        # SEARCH FOR QUERY HERE #
        return results

# handles the authorization and interfacing with the youtube api
class Youtube():

    # creates a youtube authorization object
    def __init__(self):
        flow = Flow.from_client_secrets_file(
            Config.YOUTUBE_CLIENT_SECRETS_FILE,
            scopes=Config.YOUTUBE_SCOPES)

        # sets the redirect url for google to send the user back to
        flow.redirect_uri = url_for(
            'auth_external.auth_redirect',
            _external=True,
            service='youtube')

        # creates the authorization_url to route to
        self.auth_url, self.state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true')

        session['state'] = self.state

    # returns a valid youtube access token
    def get_token(self):
        flow = Flow.from_client_secrets_file(
            Config.YOUTUBE_CLIENT_SECRETS_FILE,
            scopes=[Config.YOUTUBE_SCOPES],
            state=session['state'])

        flow.redirect_uri = url_for('auth_external.auth_redirect', _external=True, service='youtube')

        # fetches a token from google and stores its credentials
        print('=======================================')
        print(request.url)
        print('=======================================')
        flow.fetch_token(authorization_response=request.url)

        # stores the relevant token data into the session
        flask.session['yt_token_info'] = {
            'token': flow.credentials.token,
            'refresh_token': flow.credentials.refresh_token,
            'token_uri': flow.credentials.token_uri,
            'client_id': flow.credentials.client_id,
            'client_secret': flow.credentials.client_secret,
            'scopes': flow.credentials.scopes}

        return token_info

    # creates an interface to interact with youtube
    def create_api(self):
        # tries to get token data
        try:
            token_info = self.get_token()
            self.api = build('youtube', Config.YOUTUBE_API_VERSION, credentials=self.credentials)
        except:
            self.api = None

    # returns search results for a given query
    def search(self, query):
        request = self.api.search().list(part='snippet', q=query)
        response = request.execute()

        return response
