import os
#import pickle
from app.auth_external import bp, services
from flask import redirect, url_for, session, request, flash
from flask_login import current_user, login_required
from app import db
from app.misc import misc
from app.models import Service

# a universal path for logging into services
@bp.route('/auth_login/<service>', methods=['GET', 'POST'])
@login_required
def auth_login(service):
    # if request.method == 'POST'
    if current_user.is_authenticated:
        misc.clear_cache() # clears cache to prevent old token reuse

        # authorizes with a specific service
        if service == 'spotify':
            sp = services.Spotify() # creates a new spotify authorization object
            return redirect(sp.auth_url)

        elif service == 'youtube':
            # youtube database value associated with the current user
            db_yt = Service.query.filter_by(
                user_id=current_user.id,
                name='youtube').first()

            # if credentials exist for the user already
            if db_yt.credentials:
                # load credentials from database
                session['yt_token_info'] = db_yt.credentials

                flash('Logged into Youtube Successfully!')
                return redirect(url_for('main.index'))
            else:
                # resets youtube auth to blank slate when loggin in
                if 'yt_state' in session:
                    session['yt_state'] = None

                yt = services.Youtube() # creates a new youtube authorization object
                return redirect(yt_auth.auth_url)
    else:
        flash('Please log in to access this page')
        return redirect(url_for('auth_internal.login'))

# redirects user after logging in and adds them to the user database
@bp.route("/auth_redirect/<service>")
def auth_redirect(service):
    if current_user.is_authenticated:
        if service == 'spotify':
            db_sp = Service.query.filter_by(
                user_id=current_user.id,
                name='spotify').first()

            sp = services.Spotify()

            code = request.args.get('code') # gets code from response URL
            token_info = sp.oauth.get_access_token(code) # uses code sent from Spotify to exchange for an access & refresh token
            session['sp_token_info'] = token_info # saves token info into the the session
            db_sp.credentials = token_info

            # creates a spotify api object to interface with
            sp.create_api()
            if sp.api == None:
                flash('ERROR AE.R.41')
                return redirect(url_for('main.index'))

            # saves the user's spotify username into the session
            session['spotify_username'] = sp.api.current_user()['display_name']

            flash('Logged into Spotify Successfully!')
            return redirect(url_for('main.index'))
        elif service == 'youtube':
            # if google servers return an error
            if request.args.get('error'):
                error = request.args.get('error')
                flash(f'An error occurred while logging into Youtube: {error}')
                return redirect(url_for('main.index'))

            # creates a new youtube auth object with code from google servers
            yt = services.Youtube()

            # retrieves the access and refresh tokens from google servers
            token_info = yt.get_token()

            # inserts the pickled token info into the database to prevent the user  from relogging in
            Service.query.filter_by(
                user_id=current_user.id,
                name='youtube').first().credentials = pickle(token_info)

            flash('Logged into Youtube Successfully!')
            return redirect(url_for('main.index'))
    else:
        flash('Please log in to access this page')
        return redirect(url_for('auth_internal.login'))
