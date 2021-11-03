from flask import Blueprint

bp = Blueprint('playlists', __name__)

from app.playlists import forms, routes
