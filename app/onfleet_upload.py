from flask import current_app


def send_data(data, onfleet=None):
    if onfleet is None:
        onfleet = current_app.extensions["onfleet"]
    print(onfleet.tasks.get(queryParams={"from": 1621442960000}))
