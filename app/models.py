#import jwt
#import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from app import db, login
from flask import current_app
from config import Config
from sqlalchemy import delete

# EXAMPLE QUERY FOR FUTURE REFERENCE
# u.services.filter_by(name='spotify').first().id
# outputs the spotify service entry for a specific user

#--- Association Tables ---#

# association table connecting playlists and tracks
# is used to prevent duplication of tracks if one track is used in multiple playlists
playlist_track = db.Table('playlist_track',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
    db.Column('track_pos', db.Integer)
)

# association table connecting playlists and sources
playlist_source = db.Table('playlist_source',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('source_id', db.Integer, db.ForeignKey('source.id'))
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

    # keeps a user's list of supported services up-to-date
    def refresh_services(self):
        user_services = [s.name for s in self.services] # list of already initialized services for user

        # loops through supported services and adds new service to user if it doesn't exist
        for service in Config.SUPPORTED_SERVICES:
            if service not in user_services:
                db.session.add(Service(user_id=self.id, name=service))

        # loops through current user services (if any) and makes sure there are no unsupported services
        for service in user_services:
            if service not in Config.SUPPORTED_SERVICES:
                db.session.delete(Service.query.filter_by(user_id=self.id, name=service).first())

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
    art = db.Column(db.String(140))
    sources = db.relationship(
        'Source',
        secondary=playlist_source,
        back_populates='playlists',
        lazy='dynamic')
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
        return self.tracks.filter_by(
            service_id=track.service_id).first()

    # adds a source to the list of playlist sources
    def add_source(self, source):
        if not self.contains_source(source):
            self.sources.append(source)

    # removes a source from the playlist
    def remove_source(self, source):
        if self.contains_source(source):
            if self.contains_source(source):
                self.sources.remove(source)

    # returns true/false depending on whether a given source exists in the playlist
    def contains_source(self, source):
        return self.sources.filter_by(
            service_id=source.service_id).first()

# stores dynamic sources of a playlist and their options
# a sources is defined as playlist hosted on an external service
class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(32))
    service_id = db.Column(db.String(64))
    playlists = db.relationship(
        'Playlist',
        secondary=playlist_source,
        back_populates='sources',
        lazy='dynamic')
    tracks = db.relationship('Track', backref='source', lazy='dynamic')

    def __repr__(self):
        return '<Source for playlist {}, Service {}, Options {}>'.format(
            self.playlist_id, self.service, self.options)

# stores information on a track hosted on a specific service
class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # pos = db.Column(db.Integer) # the position of the track in the playlist
    service = db.Column(db.String(32)) # name of the service the track is on
    service_id = db.Column(db.String(64)) # track id on the corresponding service
    source_id = db.Column(db.String(64), db.ForeignKey('source.id')) # id of the external playlist this track is on
    title = db.Column(db.String(128))
    art = db.Column(db.String(1024)) # track artwork
    href = db.Column(db.String(1024)) # track external link
    album_id = db.Column(db.Integer, db.ForeignKey('album.id')) # album the track is on
    artists = db.relationship(
        'Artist',
        secondary=track_artist,
        back_populates='tracks',
        lazy='dynamic') # list of artists that created the track
    playlists = db.relationship(
        'Playlist',
        secondary=playlist_track,
        back_populates='tracks',
        lazy='dynamic') # list of playlists the track is on

    def __repr__(self):
        return '<Track {}, Service {}>'.format(
            self.title, self.service)

    # links a track to its artists
    def add_artist(self, name, service_id, href=None):
        if not Artist.query.filter_by(name=name, service_id=service_id).first():
            # if the artist does not exists in the database, add them
            a = Artist(
                name=name,
                service_id=service_id,
                service=self.service,
                href=href)
            db.session.add(a)

        # adds the artist to the track's list of artists
        self.artists.append(
            Artist.query.filter_by(
                name=name,
                service_id=service_id).first())

        db.session.commit()

    # links the track to its album
    def add_album(self, title, service_id, href):
        # queries the db for the album
        album = Album.query.filter_by(title=title, service_id=service_id).first()

        if not album:
            # if the album does not exists in the database, add it
            album = Album(
                title=title,
                service_id=service_id,
                service=self.service)
            db.session.add(album)

        self.album_id = Album.query.filter_by(title=title, service_id=service_id).first().id

        db.session.commit()

# stores infromation about an album
class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    service = db.Column(db.String(32)) # name of the service the track is on
    service_id = db.Column(db.String(64)) # album id on the corresponding service
    href = db.Column(db.String(1024)) # album external link
    tracks = db.relationship('Track', backref='album', lazy='dynamic')
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
        elif self.service == 'youtube':
            return #YOUTUBE ART

    # returns link to artist page
    def link(self):
        if self.service == 'spotify':
            return #SPOTIFY LINK
        elif self.service == 'youtube':
            return #YOUTUBE LINK

# stores information about an artist
class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    service_id = db.Column(db.String(256))
    service = db.Column(db.String(32))
    href = db.Column(db.String(1024)) # artist external link
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
        elif self.service == 'youtube':
            return #YOUTUBE ART

    # returns link to album page
    def link(self):
        if self.service == 'spotify':
            return #SPOTIFY LINK
        elif self.service == 'youtube':
            return #YOUTUBE LINK

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
