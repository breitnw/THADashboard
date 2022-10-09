import os
from flask import Flask, redirect, render_template
from flask_redis import FlaskRedis
from onfleet import Onfleet

from app.auth import login_required, editor_required


def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        REDIS_URL=os.environ.get('REDIS_URL', 'redis://redis_db:6379'),
        ONFLEET_API_KEY=os.environ.get('ONFLEET_API_KEY'),
    )

    # initialize Redis and Onfleet
    FlaskRedis(app, decode_responses=True)
    app.extensions["onfleet"] = Onfleet(app.config["ONFLEET_API_KEY"])

    # the home page
    @app.route('/')
    @editor_required
    def index():
        return render_template('index.html')

    from . import auth
    app.register_blueprint(auth.bp)

    from . import map
    app.register_blueprint(map.bp)
    map.init_app()

    from . import onfleet
    app.register_blueprint(onfleet.bp)

    return app
