from flask_wtf import FlaskForm # imports base flask_wtf class
from wtforms import SubmitField
from wtforms.validators import ValidationError

class EmptyForm(FlaskForm):
    submit = SubmitField('Click Here')
