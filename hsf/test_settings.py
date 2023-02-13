# Settings used when running tests in Travis
from .settings import *

GOCARDLESS_ENVIRONMENT = "sandbox"
GOCARDLESS_WEBHOOK_SECRET = ""
GOCARDLESS_ACCESS_TOKEN = ""

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DOMAIN = "localhost:8080"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "db",
        "PORT": "5432",
    }
}
