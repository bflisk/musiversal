from flask import render_template, flash, redirect, url_for, request, session, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func, delete
from app import db
from app.playlists import bp
from app.auth_external.services import Spotify, Youtube
from app.playlists.forms import CreatePlaylistForm, EditPlaylistForm
from app.models import *
from urllib.parse import urlparse

# Allows the user to create a new playlist, propagating it to supported services
@bp.route('/create_playlist', methods=['GET', 'POST'])
@login_required
def create_playlist():
    form = CreatePlaylistForm()

    if form.validate_on_submit():
        # creates a new playlist object with the user's parameters
        playlist = Playlist(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data)
        db.session.add(playlist)
        db.session.commit()

        # selects the id of the newly created playlist
        playlist_id = db.session.query(
            func.max(Playlist.id)).filter_by(
                user_id=current_user.id).first()[0]

        # creates the playlist on spotify
        if form.sp_create.data:
            sp = Spotify()
            sp.create_api()

            # creates the new playlist on spotify
            sp_playlist_info = sp.api.user_playlist_create(
                sp.api.current_user()['display_name'],
                form.title.data,
                public=form.sp_public.data,
                description=form.description.data)

            # creates a new source object for the spotify playlist
            source = Source(
                service_id=sp_playlist_info['id'],
                service='spotify')
            db.session.add(source)
            playlist.add_source(source)

        # creates the playlist on youtube
        if form.yt_create.data:
            yt = Youtube()
            yt.create_api()

            # creates the new playlist on youtube
            yt_playlist_info = yt.create_playlist(
                form.title.data,
                form.description.data,
                'private',
                'en')

            # creates a new source object for the youtube playlist
            source = Source(
                service_id=yt_playlist_info['id'],
                service='youtube')
            db.session.add(source)
            playlist.add_source(source)

        db.session.commit()
        flash('Playlist Created!')
        return redirect(url_for('main.index'))
    else:
        return render_template('playlists/create_playlist.html', form=form)

@bp.route('/view_playlist/<playlist_id>', methods=['GET', 'POST'])
@login_required
def view_playlist(playlist_id):
    sp = Spotify()
    sp.create_api()

    yt = Youtube()
    yt.create_api()

    form = EditPlaylistForm()

    # retrieves the playlist from the database
    playlist = Playlist.query.filter_by(
        id=playlist_id,
        user_id=current_user.id).first()

    # retrieves the updated list of sources
    sources = playlist.sources.all()

    # updates the playlist with new options
    if form.validate_on_submit():
        sources = [form.sources.data] # a list of NEW sources the user wants to add
        playlist = Playlist.query.filter_by(
            user_id=current_user.id,
            id=playlist_id) # the current playlist being edited

        # updates the playlist title
        if form.title.data:
            playlist.update({'title': form.title.data})

        # updates the playlist description
        if form.description.data:
            playlist.update({'description': form.description.data})

        # if the user is trying to add more sources to the playlist
        if sources:
            for source in sources:
                if 'spotify' in source or len(source) == 22:
                    # verifies the source and returns the service id
                    service_id = sp.get_service_id(source)
                    if not service_id:
                        flash(f'Must input playlist ID or playlist link: ({source})')
                        break

                    # checks that the service id refers to a valid spotify playlist
                    if not sp.verify_service_id(service_id):
                        flash(f'You are not following this spotify playlist or the id is incorrect: ({source})')
                        break

                    # adds the source to the database
                    if not Source.query.filter_by(service_id=service_id).first():
                        title = sp.api.playlist(playlist_id=service_id)['name']
                        art = sp.api.playlist_cover_image(playlist_id=service_id)[0]['url']
                        href = 'https://open.spotify.com/playlist/' + str(service_id)

                        source = Source(
                            service='spotify',
                            service_id=service_id,
                            title=title,
                            art=art,
                            href=href)
                        db.session.add(source)

                    playlist.first().add_source(
                        Source.query.filter_by(
                            service_id=service_id).first())
                elif 'youtube' in source or len(source) == 34:
                    # verifies the source
                    service_id = yt.get_service_id(source)
                    if not service_id:
                        flash(f'Must input playlist ID or playlist link: ({source})')
                        break

                    # checks that the service id refers to a valid youtube playlist
                    if not yt.verify_service_id(service_id):
                        flash(f'You are not following this spotify playlist or the id is incorrect: ({source})')
                        break

                    # adds the source to the database
                    source = Source(
                        service='youtube',
                        service_id=service_id)
                    db.session.add(source)
                    playlist.first().add_source(source)
                else:
                    flash(f'Not a valid sp or yt playlist link: ({source})')

        db.session.commit()

        return redirect(url_for('playlists.refresh_playlist', playlist_id=playlist_id))

    # retrieves the playlist's tracks from the db
    # tracks = playlist.tracks.all()
    playlist_length = playlist.tracks.count()

    return render_template('playlists/view_playlist.html',
        form=form, playlist=playlist, playlist_length=playlist_length, sources=sources)

# returns 15 tracks from a certain section of a playlist
@bp.route('/get_tracks/<playlist_id>/<offset>', methods=['POST'])
@login_required
def get_tracks(playlist_id, offset):
    track_schema = TrackSchema()
    artist_schema = ArtistSchema()
    album_schema = AlbumSchema()

    # Queries for 15 tracks from the playlist, ordered by their track positions
    tracks = Track.query.join(playlist_track).filter(
        playlist_track.c.playlist_id == playlist_id).order_by(
            playlist_track.c.track_pos).limit(15).offset(offset).all()

    # retrieves the playlist from the database
    playlist = Playlist.query.filter_by(
        id=playlist_id,
        user_id=current_user.id).first()

    # retrieves each track's corresponding artists and albums and serializes them
    artists = [[artist_schema.dump(a) for a in t.artists.all()] for t in tracks]
    albums = [album_schema.dump(Album.query.filter_by(id=t.album_id).first()) for t in tracks]

    # converts tracks to serializable objects
    data = [track_schema.dump(t) for t in tracks]

    # attaches relevant artist and album data to each track
    for i in range(len(data)):
        data[i].update({'artists': artists[i]})
        data[i].update({'album': albums[i]})

    return jsonify(data)

# TODOTODOTODOTODOTODOTODOTODOTODOTODOTODOTODO
@bp.route('/update_playlist/<playlist_id>', methods=['POST'])
@login_required
def update_playlist(playlist_id):
    # updates the playlist with new options
    sources = [form.sources.data] # a list of NEW sources the user wants to add
    playlist = Playlist.query.filter_by(
        user_id=current_user.id,
        id=playlist_id) # the current playlist being edited

    # updates the playlist title
    if form.title.data:
        playlist.update({'title': form.title.data})

    # updates the playlist description
    if form.description.data:
        playlist.update({'description': form.description.data})

    # if the user is trying to add more sources to the playlist
    if sources:
        for source in sources:
            if 'spotify' in source or len(source) == 22:
                # verifies the source and returns the service id
                service_id = sp.get_service_id(source)
                if not service_id:
                    flash(f'Must input playlist ID or playlist link: ({source})')
                    break

                # checks that the service id refers to a valid spotify playlist
                if not sp.verify_service_id(service_id):
                    flash(f'You are not following this spotify playlist or the id is incorrect: ({source})')
                    break

                # adds the source to the database
                if not Source.query.filter_by(service_id=service_id).first():
                    title = sp.api.playlist(playlist_id=service_id)['name']
                    art = sp.api.playlist_cover_image(playlist_id=service_id)[0]['url']
                    href = 'https://open.spotify.com/playlist/' + str(service_id)

                    source = Source(
                        service='spotify',
                        service_id=service_id,
                        title=title,
                        art=art,
                        href=href)
                    db.session.add(source)

                playlist.first().add_source(
                    Source.query.filter_by(
                        service_id=service_id).first())
            elif 'youtube' in source or len(source) == 34:
                # verifies the source
                service_id = yt.get_service_id(source)
                if not service_id:
                    flash(f'Must input playlist ID or playlist link: ({source})')
                    break

                # checks that the service id refers to a valid youtube playlist
                if not yt.verify_service_id(service_id):
                    flash(f'You are not following this spotify playlist or the id is incorrect: ({source})')
                    break

                # adds the source to the database
                source = Source(
                    service='youtube',
                    service_id=service_id)
                db.session.add(source)
                playlist.first().add_source(source)
            else:
                flash(f'Not a valid sp or yt playlist link: ({source})')

    db.session.commit()

    return redirect(url_for('playlists.refresh_playlist', playlist_id=playlist_id))

@bp.route('/view_blacklist/<playlist_id>')
@login_required
def view_blacklist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id).first()
    blacklist = playlist.blacklist.all()

    return render_template('playlists/view_blacklist.html', playlist=playlist, blacklist=blacklist, len=len)

@bp.route('/refresh_playlist/<playlist_id>')
@login_required
def refresh_playlist(playlist_id):
    # retrieves the playlist from the database
    playlist = Playlist.query.filter_by(
        id=playlist_id,
        user_id=current_user.id).first()

    sp = Spotify()
    sp.create_api()

    yt = Youtube()
    yt.create_api()

    # loops through the db's list of sources and keeps it up-to-date
    # tries to retrieve the playlist from a service, if it doesn't exist remove it from db
    for source in playlist.sources.all():
        if source.service == 'spotify':
            # returns whether the user is following the given playlist
            response = sp.api.playlist_is_following(
                playlist_id=source.service_id,
                user_ids=[sp.api.current_user()['display_name']])

            # checks if the source still exists
            if response[0] == False:
                # removes the tracks that were on the source from the db
                playlist_tracks = playlist.tracks.all()
                source_tracks = source.tracks.all()
                to_delete_tracks = set(playlist_tracks) & set(source_tracks)

                for track in to_delete_tracks:
                    playlist.remove_track(track)

                # if the user is not following the playlist
                playlist.remove_source(source)
            else:
                # updates playlist art
                source.art = sp.api.playlist_cover_image(playlist_id=source.service_id)[0]['url']

                # if the service id is no longer valid, remove the source and it's associated tracks
                if not sp.verify_service_id(source.service_id):
                    # queries for tracks attached to the source to be removed
                    # and removes the tracks
                    source_tracks = source.tracks.all()
                    for track in source_tracks:
                        playlist.remove_track(track)

                    # removes the source from the playlist
                    playlist.remove_source(source)

                # if the user is following the playlist, retrieve tracklist
                sp_tracks = sp.get_tracks(source.service_id)

                # retrieves the trackslist associated with the source and playlist from db
                source_tracks = source.tracks.all()
                playlist_tracks = playlist.tracks.filter_by(
                    service='spotify').all()
                db_tracks = set(playlist_tracks) & set(source_tracks)

                # parses the tracklists for just the titles
                sp_tracks_ids = [track['track']['id'] for track in sp_tracks]
                db_tracks_ids = [track.service_id for track in db_tracks]

                """
                loops through tracklist of the spotify playlist and
                checks if each track is in the database or not. It adds a track
                to the database if it does not yet exist
                """
                for track in sp_tracks:
                    if not track['track']['id'] in db_tracks_ids:
                        # if the track is not in the list of local playlist tracks
                        sp.add_track_to_playlist(playlist, source, track)

                """
                loops through tracklist of the musiversal playlist and
                checks if each track is in the list of spotify tracks.
                It removes a track from the musiversal playlist if it
                does not exist in the spotify tracklist.
                """
                for track in db_tracks:
                    if not track.service_id in sp_tracks_ids:
                        # if the track is not in the spotify tracklist
                        playlist.remove_track(track)


        elif source.service == 'youtube':
            # tries to retrieve the playlist from youtube
            request = yt.api.playlists().list(
                part='id',
                id=source.service_id)
            response = request.execute()

            # if the source doesn't exist, delete the source from db
            if response['pageInfo']['totalResults'] == 0:
                # TODO delete playlist_source assciation rows
                d = delete(Source).where(Source.id == source.id)
                db.session.execute(d)
            else:
                # if the playlist still exists, retrieve tracklist
                yt_tracks = yt.get_tracks(source.service_id)

                # retrieves the trackslist associated with the source and playlist from db
                source_tracks = source.tracks.all()
                playlist_tracks = playlist.tracks.filter_by(
                    service='youtube').all()
                db_tracks = set(playlist_tracks) & set(source_tracks)

                # parses the tracklists for just the names
                yt_tracks_ids = [track['snippet']['resourceId']['videoId'] for track in yt_tracks]
                db_tracks_ids = [track.service_id for track in db_tracks]

                """
                loops through tracklist of the youtube playlist and
                checks if each track is in the database or not. It adds a track
                to the database if it does not yet exist
                """
                for track in yt_tracks:
                    if not track['snippet']['resourceId']['videoId'] in db_tracks_ids:
                        # if the track is not in the list of local playlist tracks
                        yt.add_track_to_playlist(playlist, source, track)

                """
                loops through tracklist of the musiversal playlist and
                checks if each track is in the list of youtube tracks.
                It removes a track from the musiversal playlist if it
                does not exist in the youtube tracklist.
                """
                for track in db_tracks:
                    if not track.service_id in yt_tracks_ids:
                        # if the track is not in the spotify tracklist
                        playlist.remove_track(track)

    db.session.commit()

    return redirect(url_for('playlists.view_playlist', playlist_id=playlist_id))

@bp.route('/delete_playlist/<playlist_id>')
@login_required
def delete_playlist(playlist_id):
    # gets playlist id and its corresponding list of sources
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()

    # loops through linked sources and removes them from playlist sources
    sources = playlist.sources.all()
    for source in sources:
        playlist.remove_source(source)

    # deletes the playlist locally
    d = delete(Playlist).where(Playlist.id == playlist.id)
    db.session.execute(d)
    db.session.commit()

    flash(f'Deleted playlist: "{playlist.title}"')
    return redirect(url_for('main.index'))

@bp.route('/delete_source/<playlist_id>/<source_id>')
@login_required
def delete_source(playlist_id, source_id):

    playlist = Playlist.query.filter_by(
        id=playlist_id).first()
    source = Source.query.filter_by(
        id=source_id).first()

    # gets the tracks that should be deleted from the playlist \
    # by getting the intersection of all playlist tracks and \
    # all source tracks
    playlist_tracks = playlist.tracks.all()
    source_tracks = source.tracks.all()
    tracks_to_delete = set(playlist_tracks) & set(source_tracks)

    # removes tracks and source from the playlist
    for track in tracks_to_delete:
        playlist.remove_track(track)

    playlist.sources.remove(source)
    db.session.commit()

    return redirect(url_for('playlists.view_playlist', playlist_id=playlist_id))

@bp.route('/blacklist_track/<playlist_id>/<track_id>')
@login_required
def blacklist_track(playlist_id, track_id):
    playlist = Playlist.query.filter_by(
        id=playlist_id).first()

    track = Track.query.filter_by(
        id=track_id).first()

    # removes the track if the playlist exists
    if playlist and not track in playlist.blacklist:
        playlist.remove_track(track)
        playlist.blacklist.append(track)
        # db.session.execute(f"UPDATE blacklist SET reason = {"User removed"} WHERE track_id = {track.id}")
        db.session.commit()
    else:
        flash('This playlist does not exist or the track is already blacklisted')

    return redirect(url_for('playlists.view_playlist', playlist_id=playlist_id))

@bp.route('/whitelist_track/<playlist_id>/<track_id>')
@login_required
def whitelist_track(playlist_id, track_id):
    playlist = Playlist.query.filter_by(
        id=playlist_id).first()

    track = Track.query.filter_by(
        id=track_id).first()

    # removes the track if the playlist exists
    if playlist:
        playlist.blacklist.remove(track)
        db.session.commit()
    else:
        flash('This playlist does not exist')

    return redirect(url_for('playlists.refresh_playlist', playlist_id=playlist_id))
