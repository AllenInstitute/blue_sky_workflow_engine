from django.db import models

class Tagable(models.Model):
    '''Provides a simple tags field.
    '''
    tags = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )
    '''Short and human readable (internal format undefined)'''

    class Meta:
        abstract = True

