from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from datetime import datetime
from app import db
from app.main import bp

# run before every pageload
@bp.before_request
def before_request():
    # logs the last time the user interacted with the website
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

# home page
@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    services = current_user.services
    return render_template('index.html', services=services)

@bp.route('/redirect_page')
def redirect_page():
    return redirect(url_for('main.index'))
