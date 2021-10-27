from flask import Blueprint

bp = Blueprint('auth_external', __name__)

from app.auth_external import routes, services
