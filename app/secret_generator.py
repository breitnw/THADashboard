import click
import secrets
import os

from flask import current_app


@click.command('generate-secret-key')
@click.confirmation_option(prompt="Are you sure? If config.py already has a SECRET_KEY, it will be overridden.")
def generate_secret_key_command():
    """Create a config.py file in the instance folder that sets SECRET_KEY to a randomly generated string"""
    open(os.path.join(current_app.instance_path, "config.py"), "w+").close()

    new_data = ""
    with open(os.path.join(current_app.instance_path, "config.py"), "r") as f:
        added_secret = False
        for line in f:
            if line[0:10] == "SECRET_KEY":
                new_data += "SECRET_KEY = '" + secrets.token_hex() + "'\n"
                added_secret = True
            else:
                new_data += line + "\n"
        if not added_secret:
            new_data += "SECRET_KEY = '" + secrets.token_hex() + "'\n"
    with open(os.path.join(current_app.instance_path, "config.py"), "w") as f:
        f.write(new_data)
    click.echo('Generated the secret key. You can find it in ' + os.path.join(current_app.instance_path, "config.py"))
