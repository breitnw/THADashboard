# ha_project
Utilities to aid in data management for The Humanity Alliance, a Minnesota-based 501(c)(3) non-profit that aspires to create long-lasting community value.

#### Instructions for Use
You can build the project with `docker-compose build`, and run with `docker-compose up`.

When deploying to production, first run `flask generate-secret-key` to generate *config.py* in the instance folder,
containing a secret key for the application.