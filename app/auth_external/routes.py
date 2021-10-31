import os
from app.auth_external import bp, services
from flask import redirect, url_for, session, request, flash
from flask_login import current_user, login_required
from app import db
from app.misc import misc

# a universal path for logging into services
@bp.route('/auth_login/<service>', methods=['GET', 'POST'])
@login_required
def auth_login(service):
    # if request.method == 'POST'
    if current_user.is_authenticated:
        misc.clear_cache() # clears cache to prevent old token reuse

        # authorizes with a specific service
        if service == 'spotify':
            sp_auth = services.Spotify() # creates a new spotify authorization object
            return redirect(sp_auth.auth_url)
        elif service == 'youtube':
            yt_auth = services.Youtube() # creates a new youtube authorization object
            return redirect(yt_auth.auth_url)
    else:
        flash('Please log in to access this page')
        return redirect(url_for('auth_internal.login'))

# Redirects user after logging in and adds them to the user database
@bp.route("/auth_redirect/<service>")
def auth_redirect(service):
    if current_user.is_authenticated:
        if service == 'spotify':
            sp = services.Spotify()

            code = request.args.get('code') # Gets code from response URL
            token_info = sp.oauth.get_access_token(code) # Uses code sent from Spotify to exchange for an access & refresh token
            session['sp_token_info'] = token_info # Saves token info into the the session

            # creates a spotify api object to interface with
            sp.create_api()
            if sp.api == None:
                flash('ERROR AE.R.41')
                return redirect(url_for('main.index'))

            # saves the user's spotify username into the session
            session['spotify_username'] = sp.api.current_user()['display_name']

            flash('Logged into Spotify successfully!')
            return redirect(url_for('main.index'))
        elif service == 'youtube':
            # if google servers return an error
            if request.args.get('error'):
                error = request.args.get('error')
                flash(f'An error occurred while logging into Youtube: {error}')
                return redirect(url_for('main.index'))

            yt = services.Youtube()
            print('-----------------------------------------------')
            print(request.args.get('state'), session.get('state'))
            print(request.args.get('state') == session.get('state'))
            print('-----------------------------------------------')
            token_info = yt.get_token()

            flash('Logged into Youtube successfully!')
            return redirect(url_for('main.index'))
    else:
        flash('Please log in to access this page')
        return redirect(url_for('auth_internal.login'))
