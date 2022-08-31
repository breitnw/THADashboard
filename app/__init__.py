import os
from flask import Flask, redirect, render_template
from flask_redis import FlaskRedis

from app.auth import login_required


def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # TODO: make sure to change the secret key later (see tutorial)
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        REDIS_URL='redis://redis_db:6379'
    )
    # load the instance config, if it exists
    app.config.from_pyfile('config.py', silent=True)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # initialize Redis (work in progress)
    redis_client = FlaskRedis(app, decode_responses=True)

    # the home page
    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')

    from . import auth
    app.register_blueprint(auth.bp)

    from . import map
    app.register_blueprint(map.bp)

    return app
