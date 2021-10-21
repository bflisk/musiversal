from flask import render_template, flash, redirect, url_for, request
from app import db
from app.main import bp

# home page
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

# a universal path for logging into services
@bp.route('/auth/<service>', methods=['GET', 'POST'])
def auth(service):
    if request.method == 'POST':
        if current_user.is_authenticated:
            if service == 'spotify':
                sp_oauth = current_user.log_in(service) # creates a new sp_oauth object everytime a user logs in
                auth_url = sp_oauth.get_authorize_url() # passes the authorization url into a variable
                return redirect(auth_url)
            elif service == 'soundcloud':
                return 1
            elif service == 'youtube':
                return 1
        else:
            return redirect(url_for('login.html'))

    else:
        return render_template('auth.html')

@bp.route('/redirect_page')
def redirect_page():
    return redirect(url_for('main.index'))
