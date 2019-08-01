from django.db import models
from django_fsm import FSMField, transition, can_proceed
from django.utils import timezone
from workflow_engine.models import TWO, SECONDS_IN_MIN
import logging
from traceback import format_stack


class Runnable(models.Model):
    '''Provides an running_state field using the
    `Django FSM <https://github.com/viewflow/django-fsm>`_ package.
    '''
    class STATE:
        PENDING = "PENDING"
        QUEUED = "QUEUED"
        RUNNING = "RUNNING"
        FINISHED_EXECUTION = "FINISHED_EXECUTION"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
        FAILED_EXECUTION = "FAILED_EXECUTION"
        PROCESS_KILLED = "PROCESS_KILLED"

    _log = logging.getLogger('workflow_engine.mixins.runnable')

    run_state = models.ForeignKey(
        'workflow_engine.RunState'
    )
    '''deprecated for running state'''

    running_state = FSMField(default=STATE.PENDING)
    '''runnable objects automatically get a database field added'''

    start_run_time = models.DateTimeField(
        null=True,
        blank=True
    )

    end_run_time = models.DateTimeField(
        null=True,
        blank=True
    )

    duration = models.DurationField(
        null=True,
        blank=True
    )

    error_message = models.TextField(
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

    @classmethod
    def get_run_state_names(cls):
        return [
            Runnable.STATE.PENDING,
            Runnable.STATE.QUEUED,
            Runnable.STATE.RUNNING,
            Runnable.STATE.FINISHED_EXECUTION,
            Runnable.STATE.SUCCESS,
            Runnable.STATE.FAILED,
            Runnable.STATE.FAILED_EXECUTION,
            Runnable.STATE.PROCESS_KILLED,
        ]

    @classmethod
    def get_run_state_id_for(cls, name):
        return RunState.objects.get(name=name).id

    @classmethod
    def is_failed_type_state(cls, job_state_name):
        return (
            job_state_name == Runnable.STATE.FAILED_EXECUTION or
            job_state_name == Runnable.STATE.FAILED or
            job_state_name == Runnable.STATE.PROCESS_KILLED)

    @classmethod
    def is_running_type_state(cls, job_state_name):
        return (
            job_state_name == Runnable.STATE.PENDING or
            job_state_name == Runnable.STATE.RUNNING or
            job_state_name == Runnable.STATE.QUEUED or
            job_state_name == Runnable.STATE.FINISHED_EXECUTION)

    def get_created_at(self):
        return timezone.localtime(
            self.created_at
        ).strftime(
            '%m/%d/%Y %I:%M:%S'
        )

    def get_updated_at(self):
        return timezone.localtime(
            self.updated_at
        ).strftime(
            '%m/%d/%Y %I:%M:%S'
        )

    def get_start_run_time(self):
        result = None
        if self.start_run_time != None:
            result = timezone.localtime(
                self.start_run_time).strftime('%m/%d/%Y %I:%M:%S')

        return result

    def get_end_run_time(self):
        result = None
        if self.end_run_time != None:
            result = timezone.localtime(
                self.end_run_time).strftime('%m/%d/%Y %I:%M:%S')

        return result

    def get_duration(self):
        result = None
        if self.duration != None:
            total_seconds = self.duration.seconds
            minutes = total_seconds / SECONDS_IN_MIN

            result = str(round(minutes,TWO)) + ' min'

        return result

    def set_start_run_time(self):
        self.start_run_time = timezone.now()
        self.end_run_time = None
        self.duration = None

        self.save()

    def set_end_run_time(self):
        self.end_run_time = timezone.now()
        try:
            self.duration = self.end_run_time - self.start_run_time
        except:
            pass

        self.save()


    def set_pending_state(self, quiet=False):
        self.run_state = RunState.get_pending_state()

        if can_proceed(self.reset_pending):
            self.reset_pending()
        else:
            if not quiet:
                Runnable._log.warn(
                    'Forced transition to PENDING from {} for'.format(self.running_state, self))
            self.running_state = Runnable.STATE.PENDING

        Runnable._log.info('state is now QUEUED')
        self.save()

    def set_finished_execution_state(self, quiet=False):
        self.run_state = RunState.get_finished_execution_state()

        if can_proceed(self.finish):
            self.finish()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            if not quiet:
                Runnable._log.warn(
                    'Forced transition to FINISHED_EXECUTION from {} for {}'.format(self.running_state, self))
            self.running_state = Runnable.STATE.FINISHED_EXECUTION
        else:
            self.finish()  # trigger exception

        self.save()

    def set_queued_state(self, pbs_id=None, quiet=False):
        self.run_state = RunState.get_queued_state()

        if can_proceed(self.submit_to_queue):
            self.submit_to_queue()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            if not quiet:
                Runnable._log.warn(
                    'Forced transition to QUEUED from {} for {}'.format(self.running_state, self))
                Runnable._log.info(''.join(format_stack()))
            self.running_state = Runnable.STATE.QUEUED
        else:
            Runnable.log.info("transition to QUEUED state for {}".format(self))
            self.submit_to_queue()  # trigger exception

        self.save()

    def set_failed_state(self):
        self.run_state = RunState.get_failed_state()

        if can_proceed(self.fail):
            self.fail()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            Runnable._log.warn(
                'Forced transition to FAILED from {} for {}'.format(self.running_state, self))
            self.running_state = Runnable.STATE.FAILED
        else:
            self.fail()  # trigger exception

        self.save()

    def set_failed_execution_state(self):
        self.run_state = RunState.get_failed_execution_state()

        if can_proceed(self.fail_execution):
            Runnable._log("transition to FAILED_EXECUTION from {}".format(
                self.running_state))
            self.fail_execution()
        else:
            Runnable._log.warn(
                'Forced transition to FAILED_EXECUTION from {} for {}'.format(
                    self.running_state, self))
            self.running_state = Runnable.STATE.FAILED_EXECUTION

        self.save()

    def set_running_state(self, quiet=False):
        self.run_state = RunState.get_running_state()

        if can_proceed(self.start_running):
            self.start_running()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            if not quiet:
                Runnable._log.warn(
                    'Forced transition to RUNNING from {} for {}'.format(
                        self.running_state,
                        self))
                Runnable._log.info(''.join(format_stack()))
            self.running_state = Runnable.STATE.RUNNING
        else:
            self.start_running()  # trigger exception

        self.save()

    def set_success_state(self):
        self.run_state = RunState.get_success_state()

        if can_proceed(self.succeed):
            self.succeed()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            Runnable._log.warn(
                'Forced transition to SUCCESS from {} for {}'.format(
                    self.running_state, self))
            self.running_state = Runnable.STATE.SUCCESS
        else:
            self.succeed()  # trigger exception

        self.save()

    def set_process_killed_state(self):
        self.run_state = RunState.get_process_killed_state()
        if can_proceed(self.kill_process):
            self.kill_process()
        else:
            Runnable._log.warn(
                'Forced transition to PROCESS_KILLED from {} for {}'.format(
                    self.running_state,
                    self))
            self.running_state = Runnable.STATE.PROCESS_KILLED

        self.save()

    @transition(
        field='running_state',
        source=STATE.PENDING,
        target=STATE.QUEUED
    )
    def submit_to_queue(self):
        '''Go from a ready condition to submitted to a compute resource'''
        pass

    @transition(
        field='running_state',
        source='*',
        target=STATE.PENDING
    )
    def reset_pending(self):
        '''Transition directly to a default ready state'''
        pass

    @transition(
        field='running_state',
        source=STATE.QUEUED,
        target=STATE.RUNNING
    )
    def start_running(self):
        '''Transition from a submitted state to active processing'''
        pass

    @transition(
        field='running_state',
        source=STATE.RUNNING,
        target=STATE.FINISHED_EXECUTION
    )
    def finish(self):
        '''Transition transition from active running to checking the result'''
        pass

    @transition(
        field='running_state',
        source=[STATE.RUNNING, STATE.FINISHED_EXECUTION],
        target=STATE.SUCCESS
    )
    def succeed(self):
        '''Transition from active processing to a positive finished state'''
        pass

    @transition(
        field='running_state',
        source=[STATE.RUNNING, STATE.FINISHED_EXECUTION],
        target=STATE.FAILED
    )
    def fail(self):
        '''Transition from active processing to an error finished state'''
        pass

    @transition(
        field='running_state',
        source='*',
        target=STATE.FAILED_EXECUTION
    )
    def fail_execution(self):
        '''Transition to an exceptional fault state'''
        pass

    @transition(
        field='running_state',
        source='*',
        target=STATE.PROCESS_KILLED
    )
    def kill_process(self):
        '''Force transition into an offline state'''
        pass

from workflow_engine.models import RunState