from django.db import models
from django_fsm import FSMField, transition


class Stateful(models.Model):
    class STATE:
        PENDING = "PENDING"
        PROCESSING = "PROCESSING"
        QC = "QC"
        QC_FAILED = "QC_FAILED"
        QC_PASSED = "QC_PASSED"
        DONE = "DONE"

    object_state = FSMField(default=STATE.PENDING)

    class Meta:
        abstract = True

