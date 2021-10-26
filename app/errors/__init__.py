# Configurese a blueprint for the the error module of microblog
from flask import Blueprint

bp = Blueprint('errors', __name__)

from app.errors import handlers