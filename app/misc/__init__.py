from flask import Blueprint

bp = Blueprint('misc', __name__)

from app.misc import misc
