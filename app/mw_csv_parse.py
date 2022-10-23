import requests
import pandas as pd
from datetime import datetime
from io import StringIO
from flask import current_app
import math
import os
import re

from app.constants import HUB_LOCATION_COORDS

# Set this to True to use the local copy of export.csv
USE_LOCAL_CSV = False


def get_mw_csv_and_clean(cutoff_date):
    # Get CSV data from MembershipWorks ====================================================================
    df = get_mw_csv()

    #  Strip non-numeric characters from the phone numbers =================================================
    df['Phone (cell phone preferred for delivery app and reminder texts)'] \
        = df.apply(lambda df_row: re.sub(r'[^0-9]', '',
                                         df_row['Phone (cell phone preferred for delivery app and reminder texts)']),
                   axis=1)

    #  Raise an exception for duplicate or invalid phone numbers ===========================================
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

    #  Convert the quantities in the CSV data to colors ====================================================
    df['Task Details (Bag Color)'] = math.nan

    for i, row in df.iterrows():
        if not pd.isna(row['Item: Small Bag']):
            color = 'White'
        elif not pd.isna(row['Item: Medium Bag']):
            color = 'Green'
        elif not pd.isna(row['Item: Large Bag']):
            color = 'Blue'
        else:
            raise ValueError('Bag quantities at row ' + str(i) + ' are invalid')
        df.loc[i, 'Task Details (Bag Color)'] = color

    #  Use the database to assign values to the Team and Route/Driver column ===============================
    redis_client = current_app.extensions['redis']
    df['Team'] = math.nan

    for i, row in df.iterrows():
        db_hub = redis_client.get('zip:' + str(row['Address (Postal Code)']))
        if not db_hub or db_hub == 'unassigned':
            raise ValueError(
                "Error while preparing CSV data for Onfleet: Some zipcodes have not yet been assigned to a hub.")

        # If the Route/Driver column contains one of the hub names (i.e., not an individual), clear that entry in the column
        # and add the data from the database to the Team column
        route_driver = row["Route/Driver"]
        if any(dict_hub in str(route_driver).split() for dict_hub in HUB_LOCATION_COORDS.keys()) or pd.isna(route_driver):  # TODO: doesn't work
            df.loc[i, 'Team'] = db_hub
            df.loc[i, 'Route/Driver'] = math.nan

    # Remove any orders equally or more recent than a specified cutoff date ================================
    def is_more_recent_than_cutoff(signup_date_str):
        signup_date = datetime.strptime(signup_date_str, "%b %d, %Y")
        return signup_date >= cutoff_date

    df = df[df['Date'].apply(lambda val: not is_more_recent_than_cutoff(val))]

    return df


def get_mw_csv():
    if USE_LOCAL_CSV:
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

    # Flash an error if any of the zipcodes are null
    null_zipcode_count = df['Address (Postal Code)'].isnull().sum()
    if null_zipcode_count > 0:
        raise ValueError("Error while loading CSV data from MembershipWorks: There were "
                         + str(null_zipcode_count)
                         + " value(s) in the 'Address (Postal Code)' column that could not be read.")
    return df
