#!/bin/sh
#
# Docker entrypoint script for django/web app in production.
#

set -e

python ./manage.py migrate
exec gunicorn -w 4 hsf.wsgi
