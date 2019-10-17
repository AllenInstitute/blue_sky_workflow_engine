import celery
import logging


@celery.signals.setup_logging.connect
def configure_logging_from_settings(*args, **kwargs):
    del args    # unused
    del kwargs  # unused

    from django.conf import settings

    logging.config.dictConfig(settings.LOGGING)
