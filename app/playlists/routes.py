from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_required
from app import db
from app.playlists import bp
from app.auth_external.services import Spotify, Youtube
from app.playlists.forms import CreatePlaylistForm, EditPlaylistForm
from app.models import User, Service, Playlist, Track, Artist

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

        # creates the playlist on spotify
        if form.sp_create.data:
            sp = Spotify()
            sp.create_api()
            sp.api.user_playlist_create(
                sp.api.current_user()['display_name'],
                form.title.data,
                public=form.sp_public.data,
                description=form.description.data)

        # creates the playlist on youtube
        if form.yt_create.data:
            yt = Youtube()
            yt.create_api()
            yt.create_playlist(
                form.title.data,
                form.description.data,
                'private',
                'en')

        # adds the playlist to the database
        db.session.add(playlist)
        db.session.commit()

        flash('Playlist Created!')
        return redirect(url_for('main.index'))
    else:
        return render_template('playlists/create_playlist.html', form=form)

@bp.route('/edit_playlist/<playlist_id>')
@login_required
def edit_playlist(playlist_id):
    playlist = Playlist.query.filter_by(id=playlist_id, user_id=current_user.id).first()

    form = EditPlaylistForm()

    return render_template('playlists/edit_playlist.html', form=form, playlist=playlist)
