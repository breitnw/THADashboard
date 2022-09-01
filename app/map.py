import pandas as pd
import pgeocode
import math
import json
import os

from flask import Blueprint, render_template, url_for, request, current_app

from app.auth import login_required


# TODO: load data from database table into CSV file when exporting
bp = Blueprint('map', __name__, url_prefix='/map')


# TODO: East hub zipcode may be wrong
HUB_LOCATION_ZIPCODES = {"West": 55386, "East": 55411}
zcta_polygons = {}

# Pygeocode is used to get the coordinates of each zip code
nomi = pgeocode.Nominatim('us')


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
        return url_for('index')

    # Read export.csv, containing all of the data that needs to be assigned
    # TODO: load from a global pandas table instead
    data = pd.read_csv(os.path.join(os.path.dirname(__file__), 'data', 'export.csv'))

    # Generate a dictionary with the coordinates of every hub location
    hub_location_coords = {}
    for location in HUB_LOCATION_ZIPCODES:
        query = nomi.query_postal_code(HUB_LOCATION_ZIPCODES[location])
        assert_available(query)
        hub_location_coords[location] = (query["latitude"], query["longitude"])

    # Get a list of all the unique zipcodes in the data set
    zipcodes = data.loc[:, ["Address (Postal Code)"]]
    zipcodes['Count'] = zipcodes.groupby(['Address (Postal Code)'])['Address (Postal Code)'].transform('size')
    unique_zipcodes = zipcodes.drop_duplicates()

    geojson_data = []
    hub_data = {}
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
        if redis_client.exists("zip:" + zip):
            hub_data[zip] = redis_client.get("zip:" + zip)
        else:
            hub_data[zip] = "unassigned"

        geojson_data.append(data)

    return render_template('zip_map.html', geojson_data=geojson_data, hub_data=hub_data)


def assert_available(query):
    """Raise an exception if location data can't be received for a zipcode"""
    if math.isnan(query["latitude"]) or math.isnan(query["longitude"]):
        raise ValueError("Location data unavailable for zipcode " + str(query["postal_code"]))


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
