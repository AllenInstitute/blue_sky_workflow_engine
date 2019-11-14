from django.db import models
from django_fsm import FSMField


class Stateful(models.Model):
    '''Provides an object_state field using the
    `Django FSM <https://github.com/viewflow/django-fsm>`_ package.
    
    Object states can be used for various purposes.
    
    For example, they may indicate that an object is in or has passed (or not passed) 
    a section of a workflow.
    (for example Pending, Processing or Done).
    
    They can also be used to distinguish objects at a coarse level
    (for example PASSED, FAILED).
    
    When used with a
    :class:`workflow_engine.strategies.wait_strategy.WaitStrategy`
    they can be used to indicate
    when the object can proceed to the next workflow node
    (for example MANUAL_QC, INCOMPLETE)
    '''

    PENDING = "PENDING"
    '''Default state at object creation'''

    object_state = FSMField(default=PENDING)
    '''Stateful objects automatically get a database field added'''

    class Meta:
        abstract = True

