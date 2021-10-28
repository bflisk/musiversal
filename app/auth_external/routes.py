from app.auth_external import bp, services
from flask import redirect, url_for, session, request, flash
from flask_login import current_user, login_required
from app import db

# a universal path for logging into services
@bp.route('/auth_login/<service>', methods=['GET', 'POST'])
@login_required
def auth_login(service):
    # if request.method == 'POST'
    if current_user.is_authenticated:
        if service == 'spotify':
            spotify = services.Spotify()

            sp_oauth = spotify.create_oauth() # creates a new sp_oauth
            auth_url = sp_oauth.get_authorize_url() # passes the authorization url into a variable

            return redirect(auth_url)
        elif service == 'soundcloud':
            return f'> {service} auth under construction <'
        elif service == 'youtube':
            return f'> {service} auth under construction <'
    else:
        flash('You are not logged in!')
        return redirect(url_for('auth_internal.login'))

# Redirects user after logging in and adds them to the user database
@bp.route("/auth_redirect/<service>")
def auth_redirect(service):
    if service == 'spotify':
        spotify = services.Spotify()
        sp_oauth = spotify.create_oauth() # Creates a new sp_oauth object

        code = request.args.get('code') # Gets code from response URL
        token_info = sp_oauth.get_access_token(code) # Uses code sent from Spotify to exchange for an access & refresh token
        session['sp_token_info'] = token_info # Saves token info into the the session

        sp = spotify.create_sp()
        if sp == False:
            flash('ERROR AE.R.41')
            return redirect(url_for('main.index'))

        # saves the user's spotify username into the session
        session['spotify_username'] = sp.current_user()['display_name']

        flash('Logged into Spotify successfully!')
        return redirect(url_for('main.index', _external=True))
    elif service == 'soundcloud':
        return 'no'
    elif service == 'youtube':
        return 'stop that'
