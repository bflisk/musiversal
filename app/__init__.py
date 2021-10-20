import os
from flask import Flask, request, current_app
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# create generic module instances
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    #--- App Configuration ---#
    app = Flask(__name__)
    app.config.from_object(config_class)

    # register app-specific instances
    db.init_app(app)
    migrate.init_app(app, db)

    #--- Blueprints ---#
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app import models

    return app
