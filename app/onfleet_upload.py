from flask import current_app, Blueprint, url_for, redirect, flash, request
from app.auth import editor_required
from app.mw_csv_parse import get_mw_csv_and_clean
import pandas as pd
from json.decoder import JSONDecodeError
from datetime import datetime

bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@bp.route('/create', methods=['POST'])
@editor_required
def create():
    date = datetime.strptime(request.form['cutoff-date'], "%Y-%m-%d")
    try:
        df = get_mw_csv_and_clean(date)
    except ValueError as e:
        # Redirect the user back to the home screen if the CSV file couldn't be loaded
        flash(str(e))
        return redirect(url_for("index"))

    store_supplemental_data(df)

    if current_app.config["DEBUG_MODE"]:
        return df.to_html()

    try:
        create_tasks(df)
    except ValueError as e:
        # Redirect the user back to the home screen if a worker or hub couldn't be found
        flash(str(e))
        return redirect(url_for("index"))

    return redirect("https://onfleet.com/dashboard#/table")


def create_tasks(df):
    """
    Using a pandas dataframe generated with `mw_csv_parse.get_mw_csv_and_clean()`, creates a batch of tasks and
    uploads them to Onfleet.
    """
    onfleet = current_app.extensions["onfleet"]
    tasks = []
    workers = onfleet.workers.get()
    teams = onfleet.teams.get()
    for i, row in df.iterrows():
        if not pd.isna(row["Route/Driver"]):
            worker = row["Route/Driver"]
            try:
                worker_id = next(filter(lambda w: w["name"] == worker, workers))["id"]
            except StopIteration:
                raise ValueError(
                    "Invalid worker name \'" + worker + "\' in uploaded data. All manually assigned worker names must be present in Onfleet before upload.")
            container = {
                "type": "WORKER",
                "worker": worker_id,
            }
        else:
            team = row["Team"]
            try:
                team_id = next(filter(lambda t: t["name"] == team, teams))["id"]
            except StopIteration:
                team_names = [t["name"] for t in teams]
                raise ValueError("Invalid team name in uploaded data. Available names are " + str(
                    team_names) + ", found \'" + team + "\'")
            container = {
                "type": "TEAM",
                "team": team_id,
            }
        task = {
            "destination": {
                "address": {
                    "number": row["Address (Street)"].split()[0],
                    "street": ' '.join(row["Address (Street)"].split()[1:]),
                    "city": row["Address (City)"],
                    "state": row["Address (State/Province)"],
                    "postalCode": str(row["Address (Postal Code)"]),
                    "country": row["Address (Country)"],
                },
            },
            "recipients": [{
                "name": row["Name"],
                "phone": row["Phone (cell phone preferred for delivery app and reminder texts)"],
                "notes": row["Dietary Restrictions"]
            }],
            "notes": row["Task Details (Bag Color)"],  # This might be wrong
            "quantity": row["Quantity"],
            "container": container,
        }

        # Set values that may be NaN
        apartment = row["Apartment/Unit/Room # (if applicable)"]
        if not pd.isna(apartment):
            task["destination"]["address"]["apartment"] = apartment

        addr_name = row["Destination Name (name of apartment building, hotel, etc.)"]
        if not pd.isna(addr_name):
            task["destination"]["address"]["name"] = addr_name

        task_notes = row["Special Delivery Instructions"]
        if not pd.isna(task_notes):
            task["destination"]["notes"] = task_notes

        tasks.append(task)

    try:
        onfleet.tasks.batchCreate(body={"tasks": tasks})
    except (JSONDecodeError, KeyError):
        # TODO: it's unknown why these errors occasionally occur, they might present problems in the future if ignored
        pass

def store_supplemental_data(df):
    """
    Stores the data that is not uploaded to Onfleet in Redis.

    Data is stored in the format `supplemental-data:xxxxxxxxxx`, replacing `xxxxxxxxxx` with the digits of the
    phone number.
    """
    clear_supplemental_data()

    redis_client = current_app.extensions["redis"]

    for i, row in df.iterrows():
        supplemental_data = {
            'county': row['County'],
            'referred_by': row['Referred by (Select 1)'],
            'referred_by_other_source': row['Referred by other source?'],
            'household_size': int(row['Household Size'])
        }
        redis_client.hmset(
            "supplemental-data:" + row['Phone (cell phone preferred for delivery app and reminder texts)'],
            supplemental_data)


def clear_supplemental_data():
    """Clears all supplemental data from the database."""
    redis_client = current_app.extensions["redis"]
    for key in redis_client.scan_iter("supplemental-data:*"):
        redis_client.delete(key)
