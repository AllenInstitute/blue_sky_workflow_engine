from django.db import models
from workflow_engine.mixins import (
    Archivable,
    Configurable,
    HasWellKnownFiles,
    Enqueueable,
    Nameable,
    Tagable,
    Timestamped
)

#
# TODO: database routers might be a better answer
#

class EnqueuedProxyManager(models.Manager):
    # TODO: not sure if this will cause a loop,
    # Might need to call it remote queryset
    def get_queryset(self):
        return super(EnqueuedProxyManager, self).get_queryset().using(
            self.database
        )

class EnqueuedProxy(
    Archivable,
    Configurable,
    HasWellKnownFiles,
    Enqueueable,
    Nameable,
    Tagable,
    Timestamped,
    models.Model
):
    database = models.CharField(max_length=255, null=True)

    local_objects = models.Manager()


