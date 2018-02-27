from django.db import models
import jsonfield


class Configuration(models.Model):
    json_object = jsonfield.JSONField()
