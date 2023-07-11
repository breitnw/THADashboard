# THADashboard
Utilities to aid in data management for The Humanity Alliance, a Minnesota-based 501(c)(3) non-profit that aspires to create long-lasting community value.

---

## Tools used for Phase 1

- Python libraries: 
	- Flask (webserver)
	- Werkzeug (secure authentication)
	- pandas (dataframe management)
	- pyonfleet (Onfleet API wrapper)
	- flask-redis (Flask/Redis interop)
	- requests (MembershipWorks API requests)
- JavaScript libraries:
	- Leaflet.js (map rendering and interactivity)
- Containerization: Docker
- Database: Redis
- Dataframe management: Pandas
- HTML templating: Jinja
- IDE: PyCharm

---

## Important details

You can build the project with `docker-compose build`, and run with `docker-compose up`. 

### Setting up `variables.env`

When deploying to production, first create a file named `variables.env` in the project's base directory (the same directory
as `docker-compose.yml`). The purpose of this file is to declare several critical values that either vary between computers or should be kept secret. An example `variables.env` can be found below.

```dotenv
DEBUG_MODE=True
USE_LOCAL_CSV=True

REDIS_URL="redis://127.0.0.1:6379" 

SECRET_KEY=MY_SECRET  
ONFLEET_API_KEY=MY_KEY   
MEMBERSHIPWORKS_API_URL="https://api.membershipworks.com/my_request"
```

For the line `SECRET_KEY=MY_SECRET`, replace `MY_SECRET` with a secure key. One way to generate such a key is by running `python3 -c "import secrets; print(secrets.token_hex())"`.

For `ONFLEET_API_KEY=MY_KEY`, replace `MY_KEY` with The Humanity Alliance's API key. You can retrieve this key at https://onfleet.com/ or by contacting me at breitling.nw@gmail.com

The URL in the line `ΜEMBERSHIPWORKS_ΑPI_URL="https://api.membershipworks.com/my_request"` must be customized for the developer's network, since it represents a GET request for a CSV file from MembershipWorks. This is necessary because MembershipWorks lacks a user-friendly API, so the only method to retrieve data is through the same URL you would typically use for a manual download. To retrieve this URL, I'd recommend installing the CurlWget Chrome extension, downloading the CSV file as normal, and copying the URL of the request the extension generates. It may be necessary to place this URL in quotation marks. 

`REDIS_URL` does not need to be changed; it simply represents the URL configured in `docker-compose.yml`.

### `DEBUG_ΜODE` and `USE_LOCAL_CSV`
These are the two most important variables in `variables.env` for debugging.

`DEBUG_MODE=True` may be added to `variables.env` to turn on debug mode. In debug mode, the application will never send any data to Onfleet. Instead, whenever the user submits data, the parsed dataframe will simply be displayed as HTML. This is essential for testing changes (particularly related to Phase 1) without modifying actual data that has already been added to Onfleet. 
  
The line `USE_LOCAL_CSV=True` may also, optionally, be added. If enabled, the dashboard will pull from a local copy of the MembershipWorks database, rather than the online version. This is useful for testing crashes and other issues related to new data that has been added to MembershipWorks.

### Usage with IDEs
If you're using an IDE like PyCharm, I'd recommend making a run configuration rather than always running by building the docker image. On top of avoiding compilation times, this will enable you to use Flask's very useful debug mode, which automatically refreshes the server on each save. 

While editing a run configuration, PyCharm offers the option to import environment variables from an EnvFile. By enabling this setting with `variables.env`, you can run the Redis image alone in Docker and the Flask instance from your IDE, allowing you to take advantage of Flask's debug mode. 

### Usage with Docker
No extra setup is requried to use `variables.env` when building a Docker image; this has been configured in `docker-compose.yml`. 

---

### Database structure
As mentioned earlier, the dashboard utilizes a Redis database for persistent data. The database is backed up to a Docker volume periodically, as well as whenever the server is shut down gracefully, so don't worry about losing data upon a crash or accidental shutdown. 

As of now, most of the data stored in the database will be unimportant for Phase 2, but I'll provide some basics of what's there just in case it needs to be accessed or modified. 

### Users
Of course, the database is needed to store login data. The following fields are used to do so:
- `users` corresponds to a hashmap of each user's name and ID. Each user's data is stored under their ID, assigned when they create their account. The hashmap is used to determine a user's ID, and therefore to access their data, at login. 
- `user:id` corresponds to an integer that is incremented by 1 each time a new user creates an account. The new user is assigned this value as their ID. 
- `user:by_id:*`, where `*` is any integer, corresponds with a hashmap of a user (ID `*`)'s data. The following fields are accessible in the hashmap:
	- `signup`: the signup date (currently unused)
	- `username`: the user's username
	- `password`: a hash of the user's password
	- `permissions`: the user's permission level, represented as an integer
		- 0: NO PERMISSIONS. The user may not access the dashboard, map screen, or admin panel and must first be approved by an admin. Automatically assigned after signup
		- 1: EDITOR. The user may access the dashboard and map screen, but not the admin panel.
		- 2: ADMIN. The user may access the dashboard, map screen, and admin panel.
		- 3: OWNER. Same permissions as admin. May also assign other users admin privileges. There is only one owner, and the role is assigned to the first person to create an account. 
	- `id`: the user's ID (the same ID used in the key)

### Hubs
Hubs, like users, are defined by integer IDs, allowing for them to be renamed while keeping zip code assignments. 
- `hub:id` , like `user:id`, corresponds to an integer, representing the ID of the next hub that will be created. 
- `hub:by_id:*` corresponds with a hashmap of a hub's data: The following fields are available:
	- `name`: the name of the hub
	- `lat`: the hub's latitude
	- `long`: the hub's longitude

### Zip code assignments
Each zip code is assigned to a hub, or more specifically, a hub's ID. This is done using the `zip:*` entries, where each `*` is a 5-digit zip code. Corresponding with each entry is an integer value, representing the hub that the zip code is assigned to. Zip codes are not added in the database until they are assigned to a hub. 

### Supplemental data
One important aspect of Phase 2 is matching the report CSV (retrieved from Onfleet) to the county, referral, and household size data from the original dataframe. The easiest and most reliable way to match these two data sources is by storing this "supplemental data" in the Redis database, and using recipients' phone numbers to match it to the report CSV. 

After each upload, the dashboard has already been configured to store this data in Redis via `supplemental_data:*` entries. Each entry follows the key format of `supplemental_data:XXXXXXXXXX`, where each `X` is a digit of the recipient's phone number. All hyphens, spaces, and parentheses are removed. 

Therefore, to match this data to the report CSV, you'll only have to do the following:

2. Download the report CSV with the Onfleet API and open it as a Pandas dataframe
3. Modify the phone numbers in the report dataframe to be in the format `XXXXXXXXXX`
4. Utilize the Redis entries to append the supplemental data to each row

---

### Existing Python files
The codebase currently contains the following nine Python files:

### `__init__.py`
Creates the app using Flask's *application factory* convention
- Adds environment variables to the app's *configuration*, a dictionary that can be used anywhere in the code
- Creates a `FlaskRedis` instance, allowing for easy Flask/Redis interop
- Adds the homepage render template and registers blueprints for the other pages

### `admin.py`
Handles tasks related to the admin panel. You probably won't have to modify this file at all. This panel allows administrators to add and remove hubs and modify other users' privileges. Depending on their privileges, admins may assign the roles discussed [earlier](#users) to users.

### `auth.py`
Handles tasks related to authentication and user privileges. 
- Adds `@login_required`, `@editor_required`, and `@admin_required` function wrappers
	- As their names imply, these wrappers may be placed before any endpoint function to require the user to have a certain permission level before viewing the page. 
	- `@login_required` redirects to the login page if the user is not logged in
	- `@editor_required` redirects to an "insufficient permissions" page if the user does not have editor or higher permissions, and the login page if the user is not logged in
	- `@admin_required` redirects to an "insufficient permissions" page if the user does not have admin or higher permissions, and the login page if the user is not logged in
- Adds pages for registration and logging in

### `map.py`
Handles the map screen, used to assign zip codes to hubs. Like `admin.py`, you probably won't have to modify this file. 
- For zip codes, the dashboard loads `data/zcta-20.json`, a geoJSON file representing Minnesota's zip code tabulation areas in 2020.
	- If this file ever needs to be updated, whether due to new ZCTAs or expansion of the organization beyond Minnesota, optimizations **WILL** need to be made. 
	- The new data will need to be retrieved from the U.S. Census Bureau's website, modified with a tool like https://mapshaper.org/ to reduce resolution, and optimized in some way to allow simultaneous rendering of a greater number of polygons.
- If you have any other questions about how this file works, you can contact be at breitling.nw@gmail.com

### `mw_csv_parse.py`
Handles retrieval and cleaning of CSV data from MembershipWorks. Defines two important functions:
- `get_mw_csv()` retrieves the (mostly) raw CSV file from MembershipWorks, or from local storage if the `USE_LOCAL_CSV` environment variable is set. The way this function works is super janky, but it works and you probably won't have to change it. This function will only raise an error (displayed to the end user as an error message) if one of the zipcodes is null, and cuts all zipcodes down to five digits. 
- `get_mw_csv_and_clean(cutoff_date)` makes all of the modifications necessary to prepare the dataframe for Onfleet upload. To do so, it takes the following steps:
	1. Retrieve the CSV file with `get_mw_csv()`
	2. Strip non-numeric characters from phone numbers
	3. Raise an error if there are any blank phone numbers
	4. Raise an error if there are any duplicated phone numbers
	5. Convert the quantities in the `Item: Small Bag`, `Item: Medium Bag` and `Item: Large Bag` to colors in the `Task Details (Bag Color)` column
	6. Raise an error if a zip code hasn't yet been assigned to a hub
	7. Using values stored in the Redis database from the zip code editor, assign values to the `Τeam` and `Route/Driver` columns
	8. Remove any orders equally or more recent than a specified cutoff date
	9. Return the resulting dataframe

### `onfleet_upload.py`
As the name suggests, handles uploading the aforementioned dataframe to Onfleet. 
- Defines the function `create_tasks(df)`, which converts the dataframe into the format used by the Onfleet API and submits it to Onfleet, raising errors if:
	- A worker is referenced in the CSV file and not in Onfleet, or
	- A hub (team) is referenced in the CSV file and not in Onfleet.
- Defines the `store_supplemental_data(df)` function, **which stores supplemental data in the database so that it can later be used in report generation**. As discussed earlier, [supplemental data](#supplemental-data) is stored with the user's phone number for each key and a hashmap of relevant data for each value. 
- Defines the `tasks/create` endpoint, which retrieves the cleaned CSV, stores supplemental data, attempts to create the tasks, and redirects the user to Onfleet afterward. If `DEBUG_MODE` is enabled, data will be returned as an HTML table instead of being uploaded to Onfleet. 

### `utils.py`
Defines a few random utilities used throughout the code. Not very important, and should not need to be modified. 

---

# Phase 2

The second phase of this project, as you're probably already aware, centers around automatic generation of weekly reports. Currently, the team needs to export each report from Onfleet, manually add the "supplemental" columns discussed earlier, and make a variety of other changes to visualize and analyze the results. 

The finished product of this phase should fully automate this process, generating a weekly report with all of the data the team needs. As a bare minimum, this could take the form of a spreadsheet, generated with the click of a button, that combines the Onfleet-generated report with the aforementioned [supplemental data](#supplemental-data), adding any desired calculations or features to the result. However, for convenience and accessibility, the best course of action would be to add a visualization of this data directly on the dashboard. As of now, the homescreen is mostly empty, so this would be a good place to incorporate said visualization. Of course, there should still be an option for CSV/spreadsheet export, but this addition would nonetheless be very valuable. 

This is not an exhaustive list of the tasks necessary for Phase 2, just the most significant items. If you're making changes, please speak with Heidi or another representative for more specifics on what will be required, and see below for a few other minor considerations that may be necessary moving forward.

---

## Other minor considerations

### Duplicate phone numbers
It's important to make sure the same number isn't used for multiple different signups, especially since it's used as an identifier for users in report generation. The dashboard currently displays an error message there are duplicate phone numbers present in MembershipWorks, leaving the process of cleaning the duplicates up to the user. There might be a better way to prevent this when users sign up, but it's up to you if you feel that this issue should be addressed. 

### MembershipWorks API access
Although it works, the current method for accessing the MembershipWorks API via the `get_mw_csv()` function is incredibly finicky and should be improved. If possible, see if there's a way to address this issue by creating a more reliable means of access. 

### Updates for `map.py`
As the organization expands, it may be necessary to make modifications to this file. See [`map.py`](#mappy) for additional info. 
