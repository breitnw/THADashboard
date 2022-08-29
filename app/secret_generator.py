import click
import secrets
import os

from flask import current_app


@click.command('generate-secret-key')
@click.confirmation_option(prompt="Are you sure? If config.py already exists in the instance folder, it will be erased.")
def generate_secret_key_command():
    """Create a config.py file in the instance folder that sets SECRET_KEY to a randomly generated string"""
    with open(os.path.join(current_app.instance_path, "config.py"), "w") as f:
        f.write("SECRET_KEY = '" + secrets.token_hex() + "'")
    click.echo('Generated the secret key. You can find it in ' + os.path.join(current_app.instance_path, "config.py"))