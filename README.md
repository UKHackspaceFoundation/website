[![Build Status](https://travis-ci.org/UKHackspaceFoundation/website.svg?branch=master)](https://travis-ci.org/UKHackspaceFoundation/website)

This is the website for the [UK Hackspace Foundation](hackspace.org.uk).

# Development

## Requirements
You'll need a development environment with PostgreSQL (ideally 9.5) and Python 3
(ideally 3.7).

The easiest way of getting a consistent development enviroment is to use Docker. You'll
need Docker and docker-compose installed locally (install it 
[from here](https://store.docker.com/search?type=edition&offering=community)).

## Setup

Copy `hsf/dev_settings.py.example` to `hsf/dev_settings.py`.

If you want to test payments, visit https://manage-sandbox.gocardless.com/signup to
create a GoCardless sandbox account. Create an access token and set it in dev_settings.py

## Starting the App

To get things up and running, run:

	$ docker-compose up --build

This will download and run a separate containerised Postgres instance, and will show all the logs
in the console. Once it's running, you should now be able to access your development site at 
[http://localhost:8080](http://localhost:8080). Any changes you make to your development
copy should be automatically reloaded.

If you `Ctrl+c` the process, it'll stop the containers. If you run
`docker-compose down`, it'll destroy the containers *along with your development database*.

Any emails sent by the app will be printed to the console.

## Managing Dependencies

This app uses [Pipenv](https://pipenv.readthedocs.io) to manage dependencies. If you want
to add or update dependencies, it's easiest to do so from your host machine (so 
`pip3 install pipenv` locally).

To add a new dependency:

	$ pipenv install <dependencyname>

To update all dependencies to their latest versions:

	$ pipenv install

Once you've updated dependencies, you'll need to rebuild the Docker image by re-running
`docker-compose up --build` (you don't need to run `docker-compose down`).
