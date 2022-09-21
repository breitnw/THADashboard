import requests
import pandas as pd
import math
import json
from io import StringIO
from flask import current_app, Blueprint, url_for, redirect, flash
import os
import re

from app.auth import editor_required

bp = Blueprint('data', __name__, url_prefix='/data')


@bp.route('/get')
@editor_required
def get():
    try:
        df = get_mw_csv_and_clean()
    except ValueError as e:
        # Redirect the user back to the home screen if the CSV file couldn't be loaded
        flash(str(e))
        return redirect(url_for("index"))

    return df.to_html()


def get_mw_csv_and_clean():

    ######################################
    #  Get CSV data from MembershipWorks #
    ######################################

    df = get_mw_csv()

    #############################################################
    #  Strip non-alphanumeric characters from the phone numbers #
    #############################################################

    df['Phone (cell phone preferred for delivery app and reminder texts)'] \
        = df.apply(lambda row: re.sub(r'[^0-9]', '', row['Phone (cell phone preferred for delivery app and reminder texts)']), axis=1)

    ##############################################################
    #  Raise an exception for duplicate or invalid phone numbers #
    ##############################################################

    null_phone_count = df['Phone (cell phone preferred for delivery app and reminder texts)'].isnull().sum()
    if null_phone_count > 0:
        raise ValueError("Error while loading CSV data from MembershipWorks: There were "
             + str(null_phone_count)
             + " phone numbers that could not be read.")

    duplicate_phone_s = df.duplicated('Phone (cell phone preferred for delivery app and reminder texts)')
    duplicated_number_indices = duplicate_phone_s[duplicate_phone_s].index.tolist()
    if len(duplicated_number_indices) > 0:
        raise ValueError("Error while loading CSV data from MembershipWorks: There are duplicate phone numbers at rows "
             + str(list(map(lambda x: x + 2, duplicated_number_indices)))
                         # increment indices by 2 to account for pandas series starting at 0 and excel starting at 2
             + " (Each index represents the second occurrence of a number)")

    #####################################################
    #  Convert the quantities in the CSV data to colors #
    #####################################################

    df['Task Details (Bag Color)'] = ''

    for i in range(len(df.index)):
        if not math.isnan(df.loc[i, 'Item: Small Bag']):
            color = 'White'
        elif not math.isnan(df.loc[i, 'Item: Medium Bag']):
            color = 'Green'
        elif not math.isnan(df.loc[i, 'Item: Large Bag']):
            color = 'Blue'
        else:
            raise ValueError('Bag quantities at row ' + str(i) + ' are invalid')
        df.loc[i, 'Task Details (Bag Color)'] = color

    #########################################
    #  Add data to the Notes column as JSON #
    #########################################

    # TODO: This should be added to a separate sheet in the database instead

    def if_not_null(val):
        if pd.isnull(val):
            return ''
        return val

    for i in range(len(df.index)):
        notes = {
            'notes': if_not_null(df.loc[i, 'Notes']),
            'county': if_not_null(df.loc[i, 'County']),
            'referred_by': if_not_null(df.loc[i, 'Referred by (Select 1)']),
            'referred_by_other_source': if_not_null(df.loc[i, 'Referred by other source?']),
            'household_size': int(df.loc[i, 'Household Size'])
        }
        df.loc[i, 'Notes'] = json.dumps(notes)

    ##############################################
    #  Add the hub assignments from the database #
    ##############################################

    # TODO: Raise an exception if any zipcodes are unavailable

    redis_client = current_app.extensions['redis']
    df['Team'] = df.apply(lambda row: redis_client.get('zip:' + str(row['Address (Postal Code)'])), axis=1)

    # TODO: remove any recent orders from the dataframe

    return df


def get_mw_csv():
    # Set this to True to use the local copy of export.csv
    use_local = True
    if use_local:
        with open(os.path.join(os.path.dirname(__file__), "data", "export.csv")) as f:
            data = StringIO(f.read())
    else:
        # TODO: Find a better way to do this
        headers = {
            'Host': 'api.membershipworks.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
            'Referer': 'https://membershipworks.com/',
        }
        url = 'https://api.membershipworks.com/v1/csv?SF=CqQWGT-YS7JxJ_bUsfioO19G7RRw20fxFqwfydzIOsevPF71KzKIEwB3pOXj0FhV&_rt=946706400&frm=618575991ea12250a05d87dd'
        req = requests.get(url, headers=headers)
        data = StringIO(req.text)

    df = pd.read_csv(data)
    null_zipcode_count = df['Address (Postal Code)'].isnull().sum()
    if null_zipcode_count > 0:
        raise ValueError("Error while loading CSV data from MembershipWorks: There were "
              + str(null_zipcode_count)
              + " value(s) in the 'Address (Postal Code)' column that could not be read.")
    return df