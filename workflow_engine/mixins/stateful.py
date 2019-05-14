from django.db import models
from django_fsm import FSMField


class Stateful(models.Model):
    PENDING = "PENDING"

    object_state = FSMField(default=PENDING)

    class Meta:
        abstract = True

