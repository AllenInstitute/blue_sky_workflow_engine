from django.db import models
from django.utils import timezone


class Timestamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True)

    class Meta:
        abstract = True

    def get_created_at(self):
        return timezone.localtime(self.created_at).strftime('%m/%d/%Y %I:%M:%S')

    def get_updated_at(self):
        return timezone.localtime(self.updated_at).strftime('%m/%d/%Y %I:%M:%S')

