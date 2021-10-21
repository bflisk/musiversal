from flask import Blueprint

bp = Blueprint('auth_internal', __name__)

from app.auth_internal import forms, routes
