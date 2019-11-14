from django.db import models

class ArchivableModelManager(models.Manager):
    ''' A Django
    `query manager <https://docs.djangoproject.com/en/dev/topics/db/managers/>`_
    to automatically `filter <https://docs.djangoproject.com/en/2.2/topics/db/queries/#retrieving-specific-objects-with-filters>`_ archived objects.
    '''

    def get_queryset(self):
        '''Overrides the default model manager method.

        Returns
        -------
        QuerySet
            objects that are not archived

        Notes
        -----
        See `Modifying a Manager's Initial QuerySet <https://docs.djangoproject.com/en/dev/topics/db/managers/#modifying-a-manager-s-initial-queryset>`_
        '''
        return super(ArchivableModelManager, self).get_queryset().filter(
            archived=False
        )

class Archivable(models.Model):
    '''Provides a boolean archive field that may be set to hide it
    by default from queries and
    `admin <https://docs.djangoproject.com/en/2.2/ref/contrib/admin/>`_ views.
    '''

    archived = models.NullBooleanField(default=False)
    ''' Set to True to automatically filter this object out of all queries. '''

    all_objects = models.Manager()
    ''' Convenience access to the default model manager 
    '''

    objects = ArchivableModelManager()
    ''' Override the default model manager to filter out archived objects. 
    '''

    class Meta:
        abstract = True

    def archive(self):
        ''' Set the archived field to True and save the object
        '''
        self.archived = True
        self.save()
