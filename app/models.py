#import jwt
#import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from app import db, ma, login
from flask import current_app
from config import Config
from sqlalchemy import delete, update, text
from sqlalchemy.inspection import inspect

# EXAMPLE QUERY FOR FUTURE REFERENCE
# u.services.filter_by(name='spotify').first().id
# outputs the spotify service entry for a specific user

class Serializer(object):
    def serialize(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def serialize_list(l):
        return [m.serialize() for m in l]

# association table connecting playlists and tracks
# is used to prevent duplication of tracks if one track is used in multiple playlists
playlist_track = db.Table('playlist_track',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
    db.Column('track_pos', db.Integer)
)

# each entry in this table is a track that is blacklisted on a specific table
# being blacklisted means the specific track cannot be added from any source until /
# it is un-blacklisted
blacklist = db.Table('blacklist',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
    db.Column('reason', db.String(120))
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

# association table connecting tracks and sources
track_source = db.Table('track_source',
    db.Column('track_id', db.Integer, db.ForeignKey('track.id')),
    db.Column('source_id', db.Integer, db.ForeignKey('source.id'))
)

# stores information on the user logged into universal, NOT a service attached to universal
class User(UserMixin, db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    services = db.relationship('Service', backref='user')
    playlists = db.relationship('Playlist', backref='owner', lazy='dynamic')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def serialize(self):
        d = Serializer.serialize(self)
        return d

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
class Service(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(120), default='NULL') # username ON THE SERVICE
    name = db.Column(db.String(32)) # name of the service
    credentials = db.Column(db.PickleType()) # other credentials associated with a specific service

    def __repr__(self):
        return '<Service {}, User {}, Username {}>'.format(
            self.name, User.query.filter_by(id=self.user_id), self.username)

    def serialize(self):
        d = Serializer.serialize(self)
        return d

# stores playlist information for universal playlists, NOT service-specific playlists
class Playlist(db.Model, Serializer):
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
    blacklist = db.relationship(
        'Track',
        secondary=blacklist,
        back_populates='blacklisted_on',
        lazy='dynamic')

    def __repr__(self):
        return '<Playlist {}, ID {}>'.format(
            self.title, self.id)

    def serialize(self):
        d = Serializer.serialize(self)
        return d

    # adds a track to the playlist
    def add_track(self, track):
        if not self.contains_track(track):
            self.tracks.append(track)

    # removes a track from the playlist
    # updates track_pos to be continuous
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

    # updates all track positions in playlist to make them continuous
    def refresh_track_positions(self):
        track_ids = db.session.execute(text(f'SELECT track_id FROM playlist_track WHERE playlist_id={self.id}')).all()
        for i in range(len(track_ids)):
            sql = update(playlist_track).where(
                playlist_track.c.track_id==track_ids[i][0]).where(
                    playlist_track.c.playlist_id==self.id).values(track_pos=i)
            db.session.execute(sql)

    def set_track_pos(self, track):
        # gets the position of the last track on the playlist
        last_track_pos = db.session.execute(
            f"""SELECT MAX(track_pos)
                FROM playlist_track
                WHERE playlist_id={self.id};""").first()

        # sets the track positions of new tracks in the playlist
        if last_track_pos != (None,):
            # if the playlist isn't empty, add track onto the end
            sql = update(playlist_track).where(
                playlist_track.c.track_id == track.id).where(
                    playlist_track.c.playlist_id == self.id).values(
                        track_pos=int(last_track_pos[0]) + 1)
        else:
            # if the playlist is empty, initialize track position to 0
            sql = update(playlist_track).where(
                playlist_track.c.track_id == track.id).where(
                    playlist_track.c.playlist_id == self.id).values(track_pos=0)

        db.session.execute(sql)

# stores dynamic sources of a playlist and their options
# a sources is defined as playlist hosted on an external service
class Source(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(32))
    service_id = db.Column(db.String(64))
    title = db.Column(db.String(128))
    art = db.Column(db.String(1024)) # source artwork
    href = db.Column(db.String(1024)) # source external link
    playlists = db.relationship(
        'Playlist',
        secondary=playlist_source,
        back_populates='sources',
        lazy='dynamic')
    tracks = db.relationship(
        'Track',
        secondary=track_source,
        back_populates='sources',
        lazy='dynamic')

    def __repr__(self):
        return '<Source {}, Service {}>'.format(self.service_id, self.service)

    def serialize(self):
        d = Serializer.serialize(self)
        return d

# stores information on a track hosted on a specific service
class Track(db.Model, Serializer):
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(32)) # name of the service the track is on
    service_id = db.Column(db.String(64)) # track id on the corresponding service
    title = db.Column(db.String(128))
    art = db.Column(db.String(1024)) # track artwork
    href = db.Column(db.String(1024)) # track external link
    album_id = db.Column(db.Integer, db.ForeignKey('album.id')) # album the track is on
    sources = db.relationship(
        'Source',
        secondary=track_source,
        back_populates='tracks',
        lazy='dynamic')
    artists = db.relationship(
        'Artist',
        secondary=track_artist,
        back_populates='tracks',
        lazy='dynamic')
    playlists = db.relationship(
        'Playlist',
        secondary=playlist_track,
        back_populates='tracks',
        lazy='dynamic')
    blacklisted_on = db.relationship(
        'Playlist',
        secondary=blacklist,
        back_populates='blacklist',
        lazy='dynamic')

    def __repr__(self):
        return '<Track {}, Service {}>'.format(
            self.title, self.service)

    def serialize(self):
        d = Serializer.serialize(self)
        return d

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
                service=self.service,
                href=href)
            db.session.add(album)

        self.album_id = Album.query.filter_by(title=title, service_id=service_id).first().id

        db.session.commit()

# stores infromation about an album
class Album(db.Model, Serializer):
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

    def serialize(self):
        d = Serializer.serialize(self)
        return d

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
class Artist(db.Model, Serializer):
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

    def serialize(self):
        d = Serializer.serialize(self)
        return d

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


#- Meta tables from Marchmallow -#
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        include_fk = True

class ServiceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        include_fk = True

class PlaylistSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Playlist
        include_fk = True

class SourceSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Source
        include_fk = True

class TrackSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Track

class AlbumSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Album
        include_fk = True

class ArtistSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Artist
        include_fk = True

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
