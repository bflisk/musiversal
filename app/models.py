#import jwt
#import json
#from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
# from hashlib import md5
from app import db
#from app.auth import spotify_auth, soundcloud_auth, youtube_auth
from flask import current_app

#--- Association Tables ---#

# association table connecting playlists and tracks
# is used to prevent duplication of tracks if one track is used in multiple playlists
playlist_track = db.Table('tracklist',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('track_id', db.Integer, db.ForeignKey('track.id'))
)

# association table connecting albums and artists
# allows multiple artists to be on the same album and vice versa
album_artist = db.Table('album_artist',
    db.Column('album_id', db.Integer, db.ForeignKey('album.id')),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'))
)

# association table connecting tracks and artists
# allows multiple artists to be on the same track and vice versa
track_artist = db.Table('track_artist',
    db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
    db.Column('artist_id', db.Integer, db.ForeignKey('artist.id'))
)

#--- Mixins ---#

# returns artwork and links for a given object
"""class InfoMixin(object):
    @classmethod
    def art(cls):
        return #ARTWORK

    @classmethod
    def link(cls):
        return #LINK"""

#--- Non-association Tables ---#

# stores information on the user logged into universal, NOT a service attached to universal
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    services = db.relationship('Service', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    # Sets the password hash for the user given a password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Checks a given password against the stored password hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # creates new service fields for the given user
    def initialize_services(self, services):
        for service in services:
            # checks if the service is already in the user's list of services
            if not self.services.query.filter_by(name=service):
                svc = Service(user_id=self.id, name=service)
                db.session.add(svc)

        db.session.commit()

    # logs into a specified service
    # returns true/false based on success or failure
    def log_in(self, service):
        if service == 'spotify':
            status = spotify_auth()
        elif service == 'soundcloud':
            status = soundcloud_auth()
        elif service == 'youtube':
            status = youtube_auth()

        if status == 1:
            self.logged_in = 1

        return bool(status)

    # Creates a unique default avatar for the user using their email
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    # sends a personalized htmail message to the user
    def send_htmail(self, type):
        if type == 'stats':
            # SEND HTMAIL WITH STATISTICS
            pass
        elif type == 'recommendation':
            # SEND HTMAIL WITH RECOMMENDATIONS
            pass
        elif type == 'player':
            # SEND HTMAIL WITH FUNCTIONAL PLAYER
            pass
        elif type == 'playlist':
            # SEND HTMAIL WITH A PLAYLIST
            pass

# each row is a separate service for each separate user
# i.e. user1 has 4 service rows attached and user2 has 4 service rows attached
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(32))
    logged_in = db.Column(db.Integer, default=0)

    def __repr__(self):
        return '<Service {}, User {}, Logged in {}>'.format(
            self.name, User.query.filter_by(id=self.user_id), bool(self.logged_in))

# stores playlist information for universal playlists, NOT service-specific playlists
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(30))
    description = db.Column(db.String(140))
    tracks = db.relationship('Track', secondary=playlist_track, backref='playlist', lazy='dynamic')

    def __repr__(self):
        return '<Playlist {}, User {}>'.format(
            self.title, User.query.filter_by(id=self.user_id))

    # adds a track to the playlist
    def add_track(self, track):
        if not self.contains_track(track):
            self.tracks.append(track)

    # removes a track from the playlist
    def remove_track(self, track):
        if self.contains_track(track):
            self.tracks.remove(track)

    # returns true/false depending on whether a given track exists in the playlist
    def contains_track(self, track):
        return self.tracks.filter(
            playlist_track.c.track_id == track.id).count() > 0

# stores information on a track hosted on a specific service
class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    album = db.relationship(db.String(128), db.ForeignKey('album.title'))
    artists = db.relationship('Artist', secondary=album_artist, backref='playlist', lazy='dynamic')
    info = db.Column(db.String(2048))
    service = db.Column(db.String(32))
    playlists = db.relationship('Playlist', secondary=playlist_track, backref='track', lazy='dynamic')

    def __repr__(self):
        return '<Track {}>'.format(self.title)

    # returns track artwork
    def art(self):
        if self.service == 'spotify':
            return #SPOTIFY ART
        elif self.service == 'soundcloud':
            return #SOUNDCLOUD ART
        elif self.service == 'youtube':
            return #YOUTUBE ART

    # returns link to album page
    def link(self):
        if self.service == 'spotify':
            return #SPOTIFY LINK
        elif self.service == 'soundcloud':
            return #SOUNDCLOUD LINK
        elif self.service == 'youtube':
            return #YOUTUBE LINK

# stores infromation about an album
class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    artists = db.relationship('Artist', secondary=album_artist, backref='playlist', lazy='dynamic')

    def __repr__(self):
        return '<Album {}>'.format(self.title)

    # returns artist profile picture
    def art(self):
        if self.service == 'spotify':
            return #SPOTIFY ART
        elif self.service == 'soundcloud':
            return #SOUNDCLOUD ART
        elif self.service == 'youtube':
            return #YOUTUBE ART

    # returns link to artist page
    def link(self):
        if self.service == 'spotify':
            return #SPOTIFY LINK
        elif self.service == 'soundcloud':
            return #SOUNDCLOUD LINK
        elif self.service == 'youtube':
            return #YOUTUBE LINK

# stores information about an artist
class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    tracks = db.relationship('Track', secondary=track_artist, backref='playlist', lazy='dynamic')
    albums = db.relationship('Album', secondary=album_artist, backref='playlist', lazy='dynamic')

    def __repr__(self):
        return '<Artist {}>'.format(self.name)

    # returns album artwork
    def art(self):
        if self.service == 'spotify':
            return #SPOTIFY ART
        elif self.service == 'soundcloud':
            return #SOUNDCLOUD ART
        elif self.service == 'youtube':
            return #YOUTUBE ART

    # returns link to album page
    def link(self):
        if self.service == 'spotify':
            return #SPOTIFY LINK
        elif self.service == 'soundcloud':
            return #SOUNDCLOUD LINK
        elif self.service == 'youtube':
            return #YOUTUBE LINK
