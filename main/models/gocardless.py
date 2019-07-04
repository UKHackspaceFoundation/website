from django.conf import settings
import gocardless_pro


# utility functions:
def get_gocardless_client():
    if not getattr(settings, "GOCARDLESS_ACCESS_TOKEN", None) or not getattr(
        settings, "GOCARDLESS_ENVIRONMENT", None
    ):
        raise Exception("No GoCardless credentials configured")
    return gocardless_pro.Client(
        access_token=settings.GOCARDLESS_ACCESS_TOKEN,
        environment=settings.GOCARDLESS_ENVIRONMENT,
    )
