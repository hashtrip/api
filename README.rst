Hashtrip Backend
---------- 

Docs can be accessed in ``/docs`` endpoint, for example when in local dev environment, you can access it in `localhost:8000/docs <(localhost:8000/docs>`_.

Requirements
----------

- MongoDB community @4.2
- Python3 ^3.7.1

Quickstart
----------

First, set environment variables and create database. For example using ``docker``: ::

    export MONGO_DB=rwdb MONGO_PORT=5432 MONGO_USER=MONGO MONGO_PASSWORD=MONGO
    docker run --name mongodb --rm -e MONGO_USER="$MONGO_USER" -e MONGO_PASSWORD="$MONGO_PASSWORD" -e MONGO_DB="$MONGO_DB" MONGO
    export MONGO_HOST=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' pgdb)
    mongo --host=$MONGO_HOST --port=$MONGO_PORT --username=$MONGO_USER $MONGO_DB

Then run the following commands to bootstrap your environment with ``poetry``: ::

    git clone https://github.com/rizanw/hashtrip
    cd hashtrip
    poetry install
    poetry shell

Then create ``.env`` file (or rename and modify ``.env.example``) in project root and set environment variables for application: ::

    touch .env
    echo "PROJECT_NAME=hashtrip backend" >> .env
    echo DATABASE_URL=mongo://$MONGO_USER:$MONGO_PASSWORD@$MONGO_HOST:$MONGO_PORT/$MONGO_DB >> .env
    echo SECRET_KEY=$(openssl rand -hex 32) >> .env
    echo ALLOWED_HOSTS='"127.0.0.1", "localhost"' >> .env

To run the web application in debug use::

    uvicorn app.main:app --reload


Deployment with Docker
----------------------

You must have ``docker`` and ``docker-compose`` tools installed to work with material in this section.
First, create ``.env`` file like in `Quickstart` section or modify ``.env.example``. ``MONGO_HOST`` must be specified as `db` or modified in ``docker-compose.yml`` also. Then just run::

    docker-compose up -d

Application will be available on ``localhost`` or ``127.0.0.1`` in your browser.

Web routes
----------

All routes are available on ``/docs`` or ``/redoc`` paths with Swagger or ReDoc.


Project structure
-----------------

Files related to application are in the ``app`` directory. ``alembic`` is directory with sql migrations.
Application parts are:

::

    app
    ├── api               - web related stuff and handle routes.
    │   └── api_v1        - endpoint version.
    │       └── endpoints - definition of error routes.
    ├── core              - application configuration, startup events, logging.
    ├── db                - db related stuff. 
    ├── models            - Business logic layer, pydantic models for this application.
    ├── services          - Application logic layer.
    └── main.py           - FastAPI application instance, creation, and configuration.

