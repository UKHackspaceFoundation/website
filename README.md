This is the website for the [UK Hackspace Foundation](hackspace.org.uk).

# Development

## Requirements
The easiest way of getting a consistent development environment is to use Docker. You'll
need Docker installed locally (install it 
[from here](https://store.docker.com/search?type=edition&offering=community)).

## Setup

Copy `hsf/dev_settings.py.example` to `hsf/dev_settings.py`.

If you want to test GoCardless payments, [there are instructions here](docs/gocardless.md).

## Starting the App

To get things up and running, run:

	$ docker compose up --build

This will download and run a separate containerised Postgres instance, and will show all the logs
in the console. Once it's running, you should now be able to access your development site at 
[http://localhost:8000](http://localhost:8000). Any changes you make to your development
copy should be automatically reloaded.

If you `Ctrl+c` the process, it'll stop the containers. If you run
`docker compose down`, it'll destroy the containers *along with your development database*.

Any emails sent by the app will be printed to the console.

## Tests

To run the linter and tests (such as they are), you can do:

	$ make test

This requires that the local Docker environment is running.

## Shell

To run the Django shell with IPython on your local environment, you can run:

	$ make shell

If you've created a user account through [http://localhost:8000/signup](http://localhost:8000/signup)
and want to make yourself an admin, the appropriate shell incantation is:

```python
from main.models.user import User
u = User.objects.all()[0]
u.is_staff = True
u.save()
```

## Managing Dependencies

This app uses [Poetry](https://python-poetry.org/) to manage dependencies. If you want
to add or update dependencies, it's easiest to do so from your host machine (so 
[install Poetry](https://python-poetry.org/docs/) locally).

To add a new dependency:

	$ poetry add <dependencyname>

To update all dependencies to their latest versions:

	$ poetry lock

Once you've updated dependencies, you'll need to rebuild the Docker image by re-running
`docker compose up --build` (you don't need to run `docker compose down`).

# Deployment

See [docs/deployment.md](docs/deployment.md) for deployment info.
