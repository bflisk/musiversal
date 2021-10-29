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
        misc.clear_cache()

        # authorizes with a specific service
        if service == 'soundcloud':
            return f'> {service} auth under construction <'
        elif service == 'spotify':
            sp = services.Spotify() # creates a new spotify object
            auth_url = sp.oauth.get_authorize_url() # used to redirect spotify to auth_redirect

            return redirect(auth_url)
        elif service == 'youtube':
            yt = services.Youtube() # creates a new youtube object

            return yt.search('blartwave')
    else:
        flash('You are not logged in!')
        return redirect(url_for('auth_internal.login'))

# Redirects user after logging in and adds them to the user database
@bp.route("/auth_redirect/<service>")
def auth_redirect(service):
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
        return redirect(url_for('main.index', _external=True))
    elif service == 'soundcloud':
        return 'no'
    elif service == 'youtube':
        return 'stop that'
