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

    form = EditPlaylistForm()

    # retrieves the playlist from the database
    playlist = Playlist.query.filter_by(
        id=playlist_id,
        user_id=current_user.id).first()
    tracks = [] # will store the trackslist of the current playlist

    # loops through the db's list of sources and keeps it up-to-date
    # tries to retrieve the playlist from a service, if it doesn't exist remove it from db
    sp = Spotify()
    sp.create_api()

    yt = Youtube()
    yt.create_api()

    # keeps the list of sources updates
    for source in playlist.sources:
        if source.service == 'spotify':
            # checks if the user is following the given playlist
            response = sp.api.user_playlist_is_following(
                playlist_owner_id=session['sp_username'],
                playlist_id=source.service_id,
                user_ids=[session['sp_username']['id']])

            if response[0] == False:
                # if the user is not following the playlist (the playlist is deleted)
                d = delete(Source).where(Source.id == source.id)
                db.session.execute(d)
            else:
                # if the the playlist still exists, retrieve tracklist
                tracks.extend(sp.get_tracks(source.service_id))

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
                title = track['snippet']['title']
                video_id = track['snippet']['resourceId']['videoId']
                art = track['snippet']['thumbnails']['default']['url']
                artist = track['snippet']['videoOwnerChannelTitle']
                artist_id = track['snippet']['videoOwnerChannelId']

                # tracks.extend(yt.get_tracks(source.service_id))

    # retrieves the updates list of sources
    sources = playlist.sources

    db.session.commit()

    # updates the playlist with new options
    if form.validate_on_submit():
        sources = [form.sources.data]
        playlist = Playlist.query.filter_by(
            user_id=current_user.id,
            id=playlist_id)

        # updates the playlist title
        if form.title.data:
            playlist.update({'title': form.title.data})

        # updates the playlist description
        if form.description.data:
            playlist.update({'description': form.description.data})

        # if the user is trying to add more sources to the playlist
        if sources:
            for source in sources:
                if 'spotify' in source:
                    # parses the url for just the playlist id
                    url = urlparse(source)
                    service_id = url.path[(url.path.find('t/') + 2):]

                    # adds the source to the database
                    source = Source(
                        playlist_id=playlist_id,
                        service='spotify',
                        service_id=service_id)
                    db.session.add(source)
                elif 'youtube' in source:
                    # parses the url for just the playlist id
                    # example url: https://www.youtube.com/playlist?list=PLMkyy7SmsPZB1ykffavxZlmT1xXtHWf8x
                    url = urlparse(source)
                    service_id = url.query[(url.query.find('=') + 1):]

                    # adds the source to the database
                    source = Source(
                        playlist_id=playlist_id,
                        service='youtube',
                        service_id=service_id)
                    db.session.add(source)
                else:
                    flash('Not a valid playlist link')

        db.session.commit()

        return redirect(url_for('playlists.view_playlist', playlist_id=playlist_id))

    return render_template('playlists/view_playlist.html',
        form=form, playlist=playlist, sources=sources, tracks=tracks)

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
