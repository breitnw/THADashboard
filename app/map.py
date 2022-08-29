import os
import pandas as pd
import pgeocode
import geopy.distance
import math
import sys

from flask import Blueprint, render_template, url_for

from app.auth import login_required

# TODO: load data from database table into CSV file when exporting

bp = Blueprint('map', __name__, url_prefix='/map')

# Contains the names and zipcodes of all of the available hub locations
# TODO: East hub zipcode may be wrong
HUB_LOCATION_ZIPCODES = {"West": 55386, "East": 55411}

# Pygeocode is used to get the coordinates of each zip code
nomi = pgeocode.Nominatim('us')


# Raise an exception if location data can't be received for a zipcode
def assert_available(query):
    if math.isnan(query["latitude"]) or math.isnan(query["longitude"]):
        raise ValueError("Location data unavailable for zipcode " + str(query["postal_code"]))


# the map page
@bp.route('/zip_code_editor')
@login_required
def zip_code_editor():
    # TODO: Load from a global pandas table or from MembershipWorks instead
    data = pd.read_csv("app" + url_for('static', filename='export.csv'))

    # Generate a dictionary with the coordinates of every hub location
    hub_location_coords = {}
    for location in HUB_LOCATION_ZIPCODES:
        query = nomi.query_postal_code(HUB_LOCATION_ZIPCODES[location])
        assert_available(query)
        hub_location_coords[location] = (query["latitude"], query["longitude"])

    # Get a list of all of the unique zipcodes in the data set
    zipcodes = data.loc[:, ["Address (Postal Code)"]]
    zipcodes['Count'] = zipcodes.groupby(['Address (Postal Code)'])['Address (Postal Code)'].transform('size')
    unique_zipcodes = zipcodes.drop_duplicates()
    # print(unique_zipcodes.to_string())


    geojson_data = []
    for index, row in unique_zipcodes.iterrows():
        code = str(row["Address (Postal Code)"])
        count = str(row["Count"])
        query = nomi.query_postal_code(code)
        data = {
            "type": "Feature",
            "properties": {
                "zip_code": code,
                "count": count,
                # TODO: load zipcode assignments from the database table, or leave them as "unassigned" if there isn't an entry
                "hub": "unassigned",
            },
            "geometry": {
                "type": "Point",
                "coordinates": [query["longitude"], query["latitude"]]
            }
        }
        geojson_data.append(data)

    print(geojson_data)
    return render_template('zip_code_map.html', geojson_data=geojson_data)
