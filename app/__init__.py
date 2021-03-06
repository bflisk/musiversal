import os
from flask import Flask, request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_marshmallow import Marshmallow

# defines a naming convention to replace unnamed SQLite columns
naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# create generic module instances
metadata = MetaData(naming_convention=naming_convention)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
bootstrap = Bootstrap()
ma = Marshmallow()
login = LoginManager()

login.login_view = 'auth_internal.login' # Indicates the function that handles logins
login.login_message = 'Please log in to access this page'


def create_app(config_class=Config):
    #--- App Configuration ---#
    app = Flask(__name__)
    app.config.from_object(config_class)

    # register app-specific instances
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login.init_app(app)
    bootstrap.init_app(app)
    ma.init_app(app)

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
