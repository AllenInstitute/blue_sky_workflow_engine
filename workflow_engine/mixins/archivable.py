from django.db import models

class ArchivableModelManager(models.Manager):
    def get_queryset(self):
        return super(ArchivableModelManager, self).get_queryset().filter(
            archived=False
        )

class Archivable(models.Model):
    archived = models.NullBooleanField(default=False)

    all_objects = models.Manager()
    objects = ArchivableModelManager()

    class Meta:
        abstract = True

    def archive(self):
        self.archived = True
        self.save()
