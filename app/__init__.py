import os
from flask import Flask, request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

# create generic module instances
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth_internal.login' # Indicates the function that handles logins
login.login_message = 'Please log in to access this page'
bootstrap = Bootstrap()

def create_app(config_class=Config):
    #--- App Configuration ---#
    app = Flask(__name__)
    app.config.from_object(config_class)

    # register app-specific instances
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bootstrap.init_app(app)

    #--- Blueprints ---#
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth_internal import bp as auth_internal_bp
    app.register_blueprint(auth_internal_bp)

    from app.auth_external import bp as auth_external_bp
    app.register_blueprint(auth_external_bp)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.misc import bp as misc_bp
    app.register_blueprint(misc_bp)

    from app.playlists import bp as playlists_bp
    app.register_blueprint(playlists_bp)

    from app import models

    return app
