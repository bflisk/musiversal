import os
from config import Config
from flask import render_template, flash, redirect, url_for, request, session
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User
from app.auth_internal import bp
from app.auth_internal.forms import LoginForm, RegistrationForm
from app.misc import misc

# displays and handles the login page
@bp.route('/login', methods=['GET', 'POST'])
def login():
	misc.clear_cache()

    # if the user has already logged in, route them to the index page
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))

	form = LoginForm() # Creates an instance of the LoginForm object in 'form'

    # attempts to retrieve user from database
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()

    	# checks the user's username and password
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect(url_for('auth_internal.login'))

		# logs user into the current session
		login_user(user, remember=form.remember_me.data)

		# keeps user's service list up-to-date
		current_user.refresh_services()
		return redirect(url_for('main.index'))

	return render_template('auth_internal/login.html', title='Sign in', form=form)

# displays and handles the registration page
@bp.route('/register', methods=['GET', 'POST'])
def register():
	misc.clear_cache()

	# checks is the user is already authenticated and routes them to the index page
	if current_user.is_authenticated:
		return redirect(url_for('main.index'))

	# creates an instance of the RegistrationForm object
	form = RegistrationForm()

	# validates the form if it's submitted
	if form.validate_on_submit():
		# creates a new user object with information from the form
		user = User(username=form.username.data, email=form.email.data)
		user.set_password(form.password.data)

		# updates the database
		db.session.add(user)
		db.session.commit()

		# intializes the user's supported services
		user.refresh_services()

		flash('Congratulations, you are now a registered user!')
		return redirect(url_for('auth_internal.login'))

	return render_template('auth_internal/register.html', title='Register', form=form)

@bp.route('/logout')
@login_required
def logout():
	misc.clear_cache()

	logout_user()
	session.clear()
	return redirect(url_for('auth_internal.login'))

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
	return redirect(url_for('auth_internal.login'))
