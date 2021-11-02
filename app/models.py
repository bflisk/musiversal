#import jwt
#import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
# from hashlib import md5
from datetime import datetime
from app import db, login
from flask import current_app

# EXAMPLE QUERY FOR FUTURE REFERENCE
# u.services.filter_by(name='spotify').first().id
# outputs the spotify service entry for a specific user

#--- Association Tables ---#

# association table connecting playlists and tracks
# is used to prevent duplication of tracks if one track is used in multiple playlists
playlist_track = db.Table('playlist_track',
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
    services = db.relationship('Service', backref='user')
    playlists = db.relationship('Playlist', backref='owner', lazy='dynamic')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    # sets password hash for user given a password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # checks given password against stored password hash
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # creates new service fields for given user
    def initialize_services(self, init_services):
        user_services = [s.name for s in self.services] # list of already initialized services for user

        # loops through init_services and adds new service to user if it doesn't exist
        for service in init_services:
            if service not in user_services:
                db.session.add(Service(name=service, user_id=self.id))

        db.session.commit()

    # Creates a unique default avatar for the user using their username
    def avatar(self, size):
        digest = md5(self.username.lower().encode('utf-8')).hexdigest()
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
    username = db.Column(db.String(120), default='NULL') # username ON THE SERVICE
    name = db.Column(db.String(32)) # name of the service
    credentials = db.Column(db.PickleType()) # other credentials associated with a specific service

    def __repr__(self):
        return '<Service {}, User {}, Username {}>'.format(
            self.name, User.query.filter_by(id=self.user_id), self.username)

# stores playlist information for universal playlists, NOT service-specific playlists
class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(30))
    description = db.Column(db.String(140))
    tracks = db.relationship(
        'Track',
        secondary=playlist_track,
        back_populates='playlists',
        lazy='dynamic')

    def __repr__(self):
        return '<Playlist {}, ID {}>'.format(
            self.title, self.id)

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
    album = db.relationship('Album', backref='track', lazy='dynamic')
    artists = db.relationship(
        'Artist',
        secondary=track_artist,
        back_populates='tracks',
        lazy='dynamic')
    info = db.Column(db.String(2048))
    service = db.Column(db.String(32))
    playlists = db.relationship(
        'Playlist',
        secondary=playlist_track,
        back_populates='tracks',
        lazy='dynamic')

    def __repr__(self):
        return '<Track {}, Service {}>'.format(
            self.title, self.service)

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
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'))
    artists = db.relationship(
        'Artist',
        secondary=album_artist,
        back_populates='albums',
        lazy='dynamic')

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
    tracks = db.relationship(
        'Track',
        secondary=track_artist,
        back_populates='artists',
        lazy='dynamic')
    albums = db.relationship(
        'Album',
        secondary=album_artist,
        back_populates='artists',
        lazy='dynamic')

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

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
