from config import Config
from time import time
from flask import session, url_for, redirect, request
from flask_login import current_user
from sqlalchemy import delete, text
from app.models import Service, Source, Track
from app import db
from urllib.parse import urlparse

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
        token_info = self.get_token()
        self.api = spotipy.Spotify(auth=token_info['access_token'])
        session['sp_username'] = self.api.current_user()
        try:
            token_info = self.get_token()
            self.api = spotipy.Spotify(auth=token_info['access_token'])
            session['sp_username'] = self.api.current_user()
        except:
            self.api = None

    # generic function that returns search results
    def search(self, type, query):
        results = self.api.search(q=query, type=type)

        return results

    # deletes the spotify playlist associated with the musiversal playlist
    def delete_playlist(self, source):

        self.api.user_playlist_unfollow(
            user=session['sp_username'],
            playlist_id=source.service_id)

        # deletes the source locally
        d = delete(Source).where(Source.id == source.id)
        db.session.execute(d)

    # gets a list of tracks from a given playlist
    def get_tracks(self, playlist_id):
        tracks = []
        offset = 0

        batch = self.api.playlist_tracks(
            playlist_id,
            limit=100,
            offset=offset)['items']

        while batch:
            for track in batch:
                tracks.append(track)

            offset += 1
            batch = self.api.playlist_tracks(
                playlist_id,
                limit=100,
                offset=offset*100)['items']

        return tracks

    # parses through a source to retrieve the service id
    def get_service_id(self, source):
        # parses the source
        if 'https' in source and 'spotify' in source:
            # parses the url for just the playlist id
            url = urlparse(source)
            service_id = url.path[(url.path.find('t/') + 2):]
        elif len(source) == 22:
            # user inputted a playlist id
            service_id = source
        else:
            return None

        return service_id

    # verifies a playlist id
    def verify_service_id(self, service_id):
        # tests the playlist link
        try:
            # test the playlist link
            self.api.playlist_is_following(
                playlist_id=service_id,
                user_ids=[self.api.current_user()['display_name']])
        except:
            # playlist link is not valid
            return None

        return True

    # adds a spotify track to a playlist
    def add_track_to_playlist(self, playlist, source, track):
        # retrieves the track from the database (if it exists)
        db_track = Track.query.filter_by(service_id=track['track']['id']).first()

        # gets the playlist's blacklisted tracks
        blacklist = playlist.blacklist.all()

        # checks if the track was previously blacklisted by the user
        if not db_track in blacklist:
            # tries to get a link to track art
            try:
                art = track['track']['album']['images'][2]['url']
            except:
                art = ''

            # tries to get external link
            try:
                href = track['track']['external_urls']['spotify']
            except:
                href = 'https://open.spotify.com'

            # if this is a new track that is not in db, create and add it
            if not db_track:
                t = Track(
                    title=track['track']['name'],
                    service='spotify',
                    service_id=track['track']['id'],
                    art=art,
                    href=href)

                # adds artists from track into the database
                artists = track['track']['artists']
                for artist in artists:
                    # tries to get the external link to the artist
                    try:
                        href = artist['external_urls']['spotify']
                    except:
                        href = 'https://open.spotify.com'

                    t.add_artist(
                        artist['name'],
                        artist['id'],
                        href)

                # tries to get the external link to album
                try:
                    href = track['track']['album']['external_urls']['spotify']
                except:
                    href = 'https://open.spotify.com'

                # links the track to its album
                t.add_album(
                    track['track']['album']['name'],
                    track['track']['album']['id'],
                    href
                )

                db.session.add(t)

            track = Track.query.filter_by(service_id=track['track']['id']).first()
            last_track_pos = db.engine.execute(f"SELECT MAX(track_pos) FROM playlist_track WHERE playlist_id={playlist.id};").first()

            # sets the track positions of new tracks in the playlist
            if last_track_pos != (None,):
                # sets track pos based on the last track in the playlist
                with db.engine.begin() as conn:
                    sql = text(
                        f"""UPDATE playlist_track
                            SET track_pos=(
                                SELECT MAX(track_pos) FROM playlist_track where playlist_id={playlist.id}) + 1
                            WHERE track_id={track.id}
                            AND playlist_id={playlist.id};""")
                    conn.execute(sql)
            else:
                # sets track pos for the first track to 0
                with db.engine.begin() as conn:
                    sql = text(
                        f"""UPDATE playlist_track
                            SET track_pos=0
                            WHERE track_id={track.id}
                            AND playlist_id={playlist.id};""")
                    conn.execute(sql)

            # adds track to this playlist and adds source to track
            playlist.add_track(track)
            track.sources.append(source)

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
        try:
            session['yt_state']
            self.state = session['yt_state'] # happens after front channel auth has been completed
        except:
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

    # creates a new playlist on youtube
    def create_playlist(self, title, description, visibility, default_language):
        request = self.api.playlists().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': title,
                    'description': description,
                },
                'status': {
                    'privacyStatus': visibility
                }
            })

        response = request.execute()

        return response

    # deletes a playlist by id
    def delete_playlist(self, source):
        # deletes the source on google servers
        request = self.api.playlists().delete(
            id=source.service_id
        )
        response = request.execute()

        # deletes the source locally
        d = delete(Source).where(Source.id == source.id)
        db.session.execute(d)

        return response

    # gets a list of tracks from a given playlist
    def get_tracks(self, playlist_id):
        tracks = []

        request = self.api.playlistItems().list(
            part='snippet',
            maxResults=50,
            playlistId=playlist_id)
        batch = request.execute()

        while True:
            for track in batch['items']:
                tracks.append(track)

            # breaks out of loop when there is no next page
            try:
                page_token = batch['nextPageToken']
            except:
                break

            request = self.api.playlistItems().list(
                part='snippet',
                maxResults=50,
                pageToken=page_token,
                playlistId=playlist_id)
            batch = request.execute()

        return tracks

    # parses through a source to retrieve the service id
    def get_service_id(self, source):
        # parses through the user's input
        if 'https' in source and 'youtube' in source:
            # parses the url for just the playlist id
            # example url: https://www.youtube.com/playlist?list=PLMkyy7SmsPZB1ykffavxZlmT1xXtHWf8x
            url = urlparse(source)
            service_id = url.query[(url.query.find('=') + 1):]
        elif len(source) == 34:
            # user inputted a playlist id
            service_id = source
        else:
            return None

        return service_id

    # verifies a playlist id/url
    # returns false if the source is not valid
    def verify_service_id(self, service_id):
        # checks if the source exists
        try:
            # test the playlist link
            pass
        except:
            # playlist link is not valid
            return None

        return True

    # adds a youtube track to a playlist
    def add_track_to_playlist(self, playlist, source, track):
        # retrieves the track from the database (if it exists)
        db_track = Track.query.filter_by(service_id=track['snippet']['resourceId']['videoId']).first()

        # gets the playlist's blacklisted tracks
        blacklist = playlist.blacklist.all()

        # checks if the track was previously blacklisted by the user
        if not db_track in blacklist:
            if not db_track:
                # tries to get a link to track art
                try:
                    art = track['snippet']['thumbnails']['default']['url']
                except:
                    art = ''

                # tries to get external link
                try:
                    href = 'https://www.youtube.com/watch?v=' + track['snippet']['resourceId']['videoId']
                except:
                    href = 'https://www.youtube.com'

                # tries to get the channel that uploaded the video
                try:
                    videoOwnerChannelTitle = track['snippet']['videoOwnerChannelTitle']
                    videoOwnerChannelId = track['snippet']['videoOwnerChannelId']
                except:
                    videoOwnerChannelTitle = ''
                    videoOwnerChannelId = ''

                # if there is a new track that is not in db, add it
                t = Track(
                    title=track['snippet']['title'],
                    service='youtube',
                    service_id=track['snippet']['resourceId']['videoId'],
                    art=art,
                    href=href)

                # adds artists from track into the database
                t.add_artist(
                    videoOwnerChannelTitle,
                    videoOwnerChannelId,
                    'https://www.youtube.com/channel/' + videoOwnerChannelId)

                db.session.add(t)

            track = Track.query.filter_by(
                title=track['snippet']['title'],
                service='youtube').first()

            # adds track to this playlist and adds source to track
            playlist.add_track(track)
            track.sources.append(source)

# https://youtube.com/playlist?list=PLVCtLXKko6G0zRGLJwnEg5OAri2HMVtcc

"""
<iframe src="{{ "https://www.youtube-nocookie.com/embed/{0}?showinfo=0&rel=0&iv_load_policy=3&fs=0&controls=0&disablekb=1".format(track.service_id) }}" width="64" height="64" frameborder="0">
</iframe>
"""
