from flask_wtf import FlaskForm # imports base flask_wtf class
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

# creates a form that allows the user to log into the site
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

# creates a form that allows the user to register
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password'),])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Register')

    # makes sure password and password2 match
    def validate_password(self, password):
        if len(password.data) < 8:
            raise ValidationError('Password must be at least 8 characters long')

    # makes sure username is not already in use
    def validate_username(self, username):
        if User.query.filter_by(username=username.data).count() > 0:
            raise ValidationError('Username already in use')

    # makes sure the email isn't already in use
    def validate_email(self, email):
        if User.query.filter_by(email=email.data).count() > 0:
            raise ValidationError('Email already in use')
