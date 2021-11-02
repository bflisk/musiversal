from config import Config
from time import time
from flask import session, url_for, redirect, request
from flask_login import current_user
from app.models import Service
from app import db

import spotipy.util as util
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

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
        # queries db for spotify value associated with the current user
        db_sp = Service.query.filter_by(
            user_id=current_user.id,
            name='spotify')

        # passes the token info from the database into a variable
        token_info = db_sp.first().credentials

        # if token does not exist or it's not valid
        if token_info != None:
            # token exists: refresh it
            # checks if token is close to expiring
            now = int(time())
            is_expired = (token_info['expires_at'] - now) < 60

            # if the token is close to expiring, refresh it
            if is_expired:
                token_info = self.oauth.refresh_access_token(token_info['refresh_token'])
        else:
            # returns none if the get_token method was called to generate a new token
            # but is not on the auth_redirect page
            try:
                request.args.get('code')
            except:
                return None

            # token does not exist: generate a new one
            code = request.args.get('code') # gets code from response URL
            token_info = self.oauth.get_access_token(code) # uses code sent from Spotify to exchange for an access & refresh token

        # stores the relevant token data into the session and database
        session['sp_token_info'] = token_info
        db_sp.update({'credentials': (token_info)})
        db.session.commit()

        return token_info

    # creates api object and passes it into itself
    def create_api(self):
        # tries to get token data, return none if unable to
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

        # makes sure that the correct state is being used
        if session['yt_state'] != None:
            self.state = session['yt_state'] # happens after front channel auth has been completed
        else:
            session['yt_state'] = self.state # if a new oauth object is being requested

    # returns a valid access token, refreshing it if needed
    def get_token(self):
        # queries db for youtube value associated with the current user
        db_yt = Service.query.filter_by(
            user_id=current_user.id,
            name='youtube')

        # passes the token info from the database into a variable
        token_info = db_yt.first().credentials

        # if token does not exist or it's not valid
        if not token_info or not token_info.valid:
            if token_info and token_info.expired and token_info.refresh_token:
                # token exists but is expired: refresh it
                token_info.refresh(Request())
            elif 'auth_redirect/youtube?state' in request.url:
                # token does not exist: generate a new one
                flow = Flow.from_client_secrets_file(
                        Config.YOUTUBE_CLIENT_SECRETS_FILE,
                        scopes=Config.YOUTUBE_SCOPES,
                        state=self.state)

                flow.redirect_uri = url_for(
                        'auth_external.auth_redirect',
                        _external=True,
                        service='youtube')

                flow.fetch_token(authorization_response=request.url)
                token_info = flow.credentials
            else:
                token_info = None

        # stores the relevant token data into the session and database
        try:
            session['yt_token_info'] =  {
                'token': db_yt.credentials.token,
                'refresh_token': db_yt.credentials.refresh_token,
                'token_uri': db_yt.credentials.token_uri,
                'client_id': db_yt.credentials.client_id,
                'client_secret': db_yt.credentials.client_secret,
                'scopes': db_yt.credentials.scopes}
        except:
            session['yt_token_info'] = None
        db_yt.update({'credentials': (token_info)})
        db.session.commit()

        return token_info

    # creates an interface to interact with youtube
    def create_api(self):
        # tries to get token data
        try:
            token_info = self.get_token()
            self.api = build('youtube', Config.YOUTUBE_API_VERSION, credentials=token_info)
        except:
            self.api = None

    # returns search results for a given query
    def search(self, query):
        request = self.api.search().list(part='snippet', q=query)
        response = request.execute()

        return response
