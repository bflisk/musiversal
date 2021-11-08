from flask_wtf import FlaskForm # imports base flask_wtf class
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Length
from app.models import Playlist

# creates a form that allows the user to log into the site
class CreatePlaylistForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(min=0, max=140)])
    sp_create = BooleanField('Create on Spotify')
    sp_public = BooleanField('Public Spotify Playlist')
    yt_create = BooleanField('Create on Youtube')
    yt_public = BooleanField('Public Youtube Playlist')
    submit = SubmitField('Create Playlist')

class EditPlaylistForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(min=0, max=140)])
    sources = StringField('Add Sources')
    submit = SubmitField('Save Changes')
