# ha_project
Utilities to aid in data management for The Humanity Alliance, a Minnesota-based 501(c)(3) non-profit that aspires to create long-lasting community value.

#### Instructions for Use
You can build the project with `docker-compose build`, and run with `docker-compose up`.

When deploying to production, first create a file named `variables.env` in the project's base directory (the same directory
as `docker-compose.yml`). Two values must be added to the file:
- Add the line `SECRET_KEY=MY_SECRET` to the file, replacing `MY_SECRET` with a secure key. One way
to generate such a key is via `python3 -c "import secrets; print(secrets.token_hex())"`.
- Add the line `ONFLEET_API_KEY=MY_KEY`, replacing MY_KEY with an API key for Onfleet.