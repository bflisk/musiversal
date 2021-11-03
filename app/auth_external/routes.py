import os
from flask import redirect, url_for, session, request, flash
from flask_login import current_user, login_required
from app import db
from app.misc import misc
from app.models import Service
from app.auth_external import bp
from app.auth_external.services import Spotify, Youtube

# a universal path for logging into services
@bp.route('/auth_login/<service>', methods=['GET', 'POST'])
@login_required
def auth_login(service):
    # if request.method == 'POST'
    if current_user.is_authenticated:
        misc.clear_cache() # clears cache to prevent old token reuse

        # authorizes with a specific service
        if service == 'spotify':
            sp = Spotify() # creates a new spotify authorization object
            token_info = sp.get_token()

            if token_info != None:
                # if credentials exist for the user, token is refreshed
                flash('Logged into Spotify Successfully!')
                return redirect(url_for('main.index'))
            else:
                # if credentials DO NOT exist for the user, continue with auth flow
                return redirect(sp.auth_url)

        elif service == 'youtube':
            # resets youtube auth state to blank slate when logging in
            session['yt_state'] = None
            yt = Youtube() # creates a new youtube authorization object
            token_info = yt.get_token() # retrieves corresponding token data for user (if it exists)

            if token_info != None:
                # if credentials exist for the user, token is refreshed
                flash('Logged into Youtube Successfully!')
                return redirect(url_for('main.index'))
            else:
                # if credentials DO NOT exist for the user, continue with auth flow
                return redirect(yt.auth_url)
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

            sp = Spotify()

            # creates a spotify api object to interface with
            sp.create_api()
            if sp.api == None:
                flash('ERROR AE.R.CREATE_API')
                return redirect(url_for('main.index'))

            # saves the user's spotify username into the session and database
            session['sp_username'] = sp.api.current_user()['display_name']
            db_sp.update({'username': (session['sp_username'])})
            db.session.commit()

            flash('Logged into Spotify Successfully!')
            return redirect(url_for('main.index'))
        elif service == 'youtube':
            # if google servers return an error
            if request.args.get('error'):
                error = request.args.get('error')
                flash(f'An error occurred while logging into Youtube: {error}')
                return redirect(url_for('main.index'))

            # creates a new youtube auth object with code from google servers
            yt = Youtube()

            # retrieves the access and refresh tokens from google servers
            token_info = yt.get_token()

            session['yt_username'] = 'fuck'

            flash('Logged into Youtube Successfully!')
            return redirect(url_for('main.index'))
    else:
        flash('Please log in to access this page')
        return redirect(url_for('auth_internal.login'))
