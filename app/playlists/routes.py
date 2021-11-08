from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_required
from sqlalchemy import func, delete
from app import db
from app.playlists import bp
from app.auth_external.services import Spotify, Youtube
from app.playlists.forms import CreatePlaylistForm, EditPlaylistForm
from app.models import User, Service, Playlist, Track, Artist, Source

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

@bp.route('/view_playlist/<playlist_id>')
@login_required
def view_playlist(playlist_id):
    # retrieves the playlist from the database
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()

    # loops through the db's list of sources and keeps it up-to-date
    # tries to retrieve the playlist from a service, if it doesn't exist remove it from db
    for source in playlist.sources:
        if source.service == 'spotify':
            sp = Spotify()
            sp.create_api()

            # checks if the user is following the given playlist
            response = sp.api.user_playlist_is_following(
                playlist_owner_id=session['sp_username'],
                playlist_id=source.service_id,
                user_ids=[session['sp_username']['id']])

            # if the user is not following the playlist (the playlist is deleted)
            if response[0] == False:
                d = delete(Source).where(Source.id == source.id)
                db.session.execute(d)
        elif source.service == 'youtube':
            # tries to retrieve the playlist from youtube
            yt = Youtube()
            yt.create_api()
            request = yt.api.playlists().list(
                part='id',
                id=source.service_id)
            response = request.execute()

            # if the source doesn't exist, delete the source from db
            if response['pageInfo']['totalResults'] == 0:
                d = delete(Source).where(Source.id == source.id)
                db.session.execute(d)

    db.session.commit()

    # retrieves the updates list of sources
    sources = playlist.sources

    form = EditPlaylistForm()

    return render_template('playlists/view_playlist.html', form=form, playlist=playlist, sources=sources)

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
