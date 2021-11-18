from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_required
from sqlalchemy import func, delete
from app import db
from app.playlists import bp
from app.auth_external.services import Spotify, Youtube
from app.playlists.forms import CreatePlaylistForm, EditPlaylistForm
from app.models import User, Service, Playlist, Track, Artist, Source
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
            sp_source = Source(
                playlist_id=playlist_id,
                service_id=sp_playlist_info['id'],
                service='spotify')
            db.session.add(sp_source)

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
            yt_source = Source(
                playlist_id=playlist_id,
                service_id=yt_playlist_info['id'],
                service='youtube')
            db.session.add(yt_source)

        db.session.commit()
        flash('Playlist Created!')
        return redirect(url_for('main.index'))
    else:
        return render_template('playlists/create_playlist.html', form=form)

@bp.route('/view_playlist/<playlist_id>', methods=['GET', 'POST'])
@login_required
def view_playlist(playlist_id):
    """
    <a href="{{ url_for('playlists.delete_playlist', playlist_id=playlist.id) }}">
    Delete Playlist
    </a>
    """
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
    sources = playlist.sources

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
                    service_id = sp.verify_source(source)
                    if len(service_id) != 22:
                        # spotify id is 22 chars long
                        flash(service_id)
                        break

                    # adds the source to the database
                    source = Source(
                        playlist_id=playlist_id,
                        service='spotify',
                        service_id=service_id)
                    db.session.add(source)

                elif 'youtube' in source or len(source) == 34:
                    # verifies the source
                    service_id = yt.verify_source(source)
                    if len(service_id) != 34:
                        # youtube id is 34 chars long
                        flash(service_id)
                        break

                    # adds the source to the database
                    source = Source(
                        playlist_id=playlist_id,
                        service='youtube',
                        service_id=service_id)
                    db.session.add(source)
                else:
                    flash(f'Not a valid sp or yt playlist link: ({source})')

        db.session.commit()

        return redirect(url_for('playlists.refresh_playlist', playlist_id=playlist_id))

    # retrieves the playlist's tracks from the db
    tracks = playlist.tracks.all()

    return render_template('playlists/view_playlist.html',
        form=form, playlist=playlist, sources=sources, tracks=tracks, len=len)

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
    for source in playlist.sources:
        if source.service == 'spotify':
            # returns whether the user is following the given playlist
            response = sp.api.playlist_is_following(
                playlist_id=source.service_id,
                user_ids=[sp.api.current_user()['display_name']])

            if response[0] == False:
                # if the user is not following the playlist
                d = delete(Source).where(Source.id == source.id)
                db.session.execute(d)

                # TODO
                # removes the tracks that were on the source from the db
                to_delete_tracks = playlist.tracks.filter_by(

                )
            else:
                # if the user is following the playlist, retrieve tracklist
                sp_tracks = sp.get_tracks(source.service_id)
                db_tracks = playlist.tracks.filter_by(
                    service='spotify',
                    source_id=source.service_id).all()

                # parses the tracklists for just the titles
                sp_tracks_titles = [track['track']['name'] for track in sp_tracks]
                db_tracks_titles = [track.title for track in db_tracks]

                """
                loops through tracklist of the spotify playlist and
                checks if each track is in the database or not. It adds a track
                to the database if it does not yet exist
                """
                for track in sp_tracks:
                    if not track['track']['name'] in db_tracks_titles:
                        # if the track is not in the list of local playlist tracks

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

                        if not Track.query.filter_by(title=track['track']['name'], service='spotify').first():
                            # if this is a new track that is not in db, add it
                            t = Track(
                                title=track['track']['name'],
                                service='spotify',
                                service_id=track['track']['id'],
                                source_id=source.service_id,
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

                        # adds track to this playlist
                        playlist.add_track(
                            Track.query.filter_by(
                                title=track['track']['name'],
                                service='spotify').first())

                """
                loops through tracklist of the musiversal playlist and
                checks if each track is in the list of spotify tracks.
                It removes a track from the musiversal playlist if it
                does not exist in the spotify tracklist.
                """
                for track in db_tracks:
                    if not track.title in sp_tracks_titles:
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
                d = delete(Source).where(Source.id == source.id)
                db.session.execute(d)
            else:
                # if the playlist still exists, retrieve tracklist
                yt_tracks = yt.get_tracks(source.service_id)
                db_tracks = playlist.tracks.filter_by(
                    service='youtube',
                    source_id=source.service_id).all()

                # parses the tracklists for just the names
                yt_tracks_titles = [track['snippet']['title'] for track in yt_tracks]
                db_tracks_titles = [track.title for track in db_tracks]

                """
                loops through tracklist of the youtube playlist and
                checks if each track is in the database or not. It adds a track
                to the database if it does not yet exist
                """
                for track in yt_tracks:
                    if not track['snippet']['title'] in db_tracks_titles:
                        if not Track.query.filter_by(title=track['snippet']['title'], service='youtube').first():
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
                                source_id=source.service_id,
                                art=art,
                                href=href)

                            # adds artists from track into the database
                            t.add_artist(
                                videoOwnerChannelTitle,
                                videoOwnerChannelId,
                                'https://www.youtube.com/channel/' + videoOwnerChannelId)

                            db.session.add(t)

                        # adds track to this playlist
                        playlist.add_track(
                            Track.query.filter_by(
                                title=track['snippet']['title'],
                                service='youtube').first())

                """
                loops through tracklist of the musiversal playlist and
                checks if each track is in the list of youtube tracks.
                It removes a track from the musiversal playlist if it
                does not exist in the youtube tracklist.
                """
                for track in db_tracks:
                    if not track.title in yt_tracks_titles:
                        # if the track is not in the spotify tracklist
                        playlist.remove_track(track)

    db.session.commit()

    return redirect(url_for('playlists.view_playlist', playlist_id=playlist_id))

@bp.route('/delete_playlist/<playlist_id>')
@login_required
def delete_playlist(playlist_id):
    sp = Spotify()
    sp.create_api()

    yt = Youtube()
    yt.create_api()

    # gets playlist id and its corresponding list of sources
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()
    sources = playlist.sources

    # loops through linked sources and deletes them
    for source in sources:
        if source.service == 'spotify':
            sp.delete_playlist(source)
        elif source.service == 'youtube':
            yt.delete_playlist(source)

    # deletes the playlist locally
    d = delete(Playlist).where(Playlist.id == playlist.id)
    db.session.execute(d)
    db.session.commit()

    flash(f'Deleted playlist: {playlist.id}')
    return redirect(url_for('main.index'))
