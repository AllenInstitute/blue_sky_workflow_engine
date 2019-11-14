from django.db import models

class Nameable(models.Model):
    '''Provides string name and description fields
    and use the name as the default string representation.
    '''

    name = models.CharField(max_length=255)
    '''Short and human readable'''

    description = models.CharField(max_length=255, null=True, blank=True)
    '''More detail and human readable'''

    class Meta:
        abstract = True

    def __str__(self):
        '''Use name as the human readable default.'''
        return self.name

