import pandas as pd
import math
import json
import os

from flask import Blueprint, render_template, url_for, request, current_app, flash, redirect

from app.auth import login_required
import app.mw_to_onfleet

# TODO: Display the following on the map screen:
# List of unassigned zip codes
# Total deliveries for each hub

# TODO: load data from database table into CSV file when exporting
bp = Blueprint('map', __name__, url_prefix='/map')

# West: 7600 Victoria drive, Victoria MN 55386
# East: 1835 North Penn Avenue, Minneapolis MN 55411
HUB_LOCATION_COORDS = {"West": (44.867340, -93.674630), "East": (44.998190, -93.308270)}
zcta_polygons = {}

# TODO: make sure authentication is required for get request
# the map page
@bp.route('/zip_editor', methods=['GET', 'POST'])
@login_required
def zip_editor():
    redis_client = current_app.extensions['redis']

    # After editing, post the data to the redis database
    if request.method == 'POST':
        new_hub_data = request.json
        for zip, hub in new_hub_data.items():
            redis_client.set("zip:" + zip, hub)
        return ""

    # Read export.csv, containing all of the data that needs to be assigned
    try:
        data = app.mw_to_onfleet.get_mw_csv()
    except ValueError as e:
        # Redirect back to the home screen if unable to load CSV data
        flash(str(e))
        return redirect(url_for('index'))

    # Get a list of all the unique zipcodes in the data set
    zipcodes = data.loc[:, ["Address (Postal Code)"]]
    zipcodes['Count'] = zipcodes.groupby(['Address (Postal Code)'])['Address (Postal Code)'].transform('size')
    unique_zipcodes = zipcodes.drop_duplicates()

    geojson_data = []
    hub_assignment_data = {}
    for index, row in unique_zipcodes.iterrows():
        zip = str(row["Address (Postal Code)"])
        count = str(row["Count"])

        data = {
            "type": "Feature",
            "properties": {
                "zip": zip,
                "count": count,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": zcta_polygons[int(zip)]
            }
        }

        # TODO: load zipcode assignments from the database table, or leave them as "unassigned" if there isn't an entry

        hub_assignment_data[zip] = "unassigned"
        if redis_client.exists("zip:" + zip):
            hub = redis_client.get("zip:" + zip)
            if hub in HUB_LOCATION_COORDS.keys():
                hub_assignment_data[zip] = redis_client.get("zip:" + zip)

        geojson_data.append(data)

    return render_template('zip_map.html',
                           geojson_data=geojson_data,
                           hub_assignment_data=hub_assignment_data,
                           hub_location_data=HUB_LOCATION_COORDS,)


def init_app():
    """When the app is initialized, set zcta_polygons to a dictionary with zip codes as keys and their respective polygons as values"""
    global zcta_polygons
    f = open(os.path.join(os.path.dirname(__file__), 'data', 'zcta-20.json'))
    geojson_dict = json.load(f)
    f.close()
    for feature in geojson_dict['features']:
        zip = int(feature['properties']['ZCTA5CE20'])
        geometry = feature['geometry']['coordinates']

        # Needed to fix a weird GeoJSON bug
        if len(geometry[0]) == 1:
            for i, sub_arr in enumerate(geometry):
                geometry[i] = sub_arr[0]

        # Add to the dictionary
        zcta_polygons[zip] = geometry
