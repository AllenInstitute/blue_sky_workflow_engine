from django.db import models

class Tagable(models.Model):
    tags = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

