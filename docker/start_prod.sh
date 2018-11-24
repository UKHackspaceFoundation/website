#!/bin/sh
#
# Docker entrypoint script for django/web app in production.
#

set -e

python ./manage.py migrate

# Ideally this would be run on build, but that would require a
# separate static server on this image. At the moment we run
# it here, which writes it out to a mounted path to be served
# by nginx on the host.
python ./manage.py collectstatic --no-input

exec gunicorn -w 4 hsf.wsgi -b 0.0.0.0:8000
