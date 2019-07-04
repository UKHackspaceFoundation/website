#!/bin/sh
#
# Docker entrypoint script for django/web app in development.
#

set -e

# Wait until postgres is available before proceeding
until PGPASSWORD=postgres psql -h "db" -U "postgres" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

python ./manage.py migrate
exec python ./manage.py runserver 0.0.0.0:8000
