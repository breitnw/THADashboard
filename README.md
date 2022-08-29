# ha_project
Utilities to aid in data management for The Humanity Alliance, a Minnesota-based 501(c)(3) non-profit that aspires to create long-lasting community value.

#### Instructions for Use
1. Initialize and enter a Python virtual environment
2. Install the requirements with `pip install -r requirements.txt`
3. Initialize the SQLite database with `flask init-db`
4. Run the project with `flask run`, or alternatively `flask --debug run` to enable live reloading

When deploying to production, first run `flask generate-secret-key` to generate *config.py* in the instance folder,
containing a secret key for the application.