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

    def in_failed_state(self):
        run_state_name = self.running_state
        return (run_state_name == Runnable.STATE.FAILED or
                run_state_name == Runnable.STATE.PROCESS_KILLED or
                run_state_name == Runnable.STATE.FAILED_EXECUTION)

    def get_color_class(self):
        color = 'color_' + self.running_state.lower()

        return color

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

    def can_rerun(self):
        run_state_name = self.running_state

        return (run_state_name == Runnable.STATE.PENDING or
                run_state_name == Runnable.STATE.FAILED or
                run_state_name == Runnable.STATE.SUCCESS or
                run_state_name == Runnable.STATE.PROCESS_KILLED or
                run_state_name == Runnable.STATE.FAILED_EXECUTION)

    def in_pending_state(self):
        return (self.running_state == Runnable.STATE.PENDING)

    def in_success_state(self):
        return (self.running_state == Runnable.STATE.SUCCESS)

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
        if can_proceed(self.reset_pending):
            self.reset_pending()
        else:
            if not quiet:
                Runnable._log.warning(
                    'Forced transition to PENDING from %s for %s',
                    self.running_state,
                    str(self))
            self.running_state = Runnable.STATE.PENDING

        Runnable._log.info('state is now QUEUED')
        self.save()

    def set_finished_execution_state(self, quiet=False):
        if can_proceed(self.finish):
            self.finish()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            if not quiet:
                Runnable._log.warning(
                    'Forced transition to FINISHED_EXECUTION from %s for %s',
                    str(self.running_state),
                    str(self)
                )
            self.running_state = Runnable.STATE.FINISHED_EXECUTION
        elif self.running_state == Runnable.STATE.FAILED_EXECUTION:
            Runnable._log.warning('Unexpected state transition - remaining in FAILED_EXECUTION')
        else:
            self.finish()  # trigger exception

        self.save()

    def set_queued_state(self, quiet=False):
        if can_proceed(self.submit_to_queue):
            self.submit_to_queue()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            if not quiet:
                Runnable._log.warning(
                    'Forced transition to QUEUED from %s for %s',
                    str(self.running_state),
                    str(self)
                )
                Runnable._log.info(''.join(format_stack()))
            self.running_state = Runnable.STATE.QUEUED
        else:
            Runnable._log.info(
                "transition to QUEUED state for %s",
                str(self)
            )
            self.submit_to_queue()  # trigger exception

        self.save()

    def set_failed_state(self):
        if can_proceed(self.fail):
            self.fail()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            Runnable._log.warning(
                'Forced transition to FAILED from %s for %s',
                str(self.running_state),
                str(self)
            )
            self.running_state = Runnable.STATE.FAILED
        else:
            self.fail()  # trigger exception

        self.save()

    def set_failed_execution_state(self):
        if can_proceed(self.fail_execution):
            Runnable._log.warning(
                "transition to FAILED_EXECUTION from %s",
                str(self.running_state)
            )
            self.fail_execution()
        else:
            Runnable._log.warning(
                'Forced transition to FAILED_EXECUTION from %s for %s',
                str(self.running_state),
                str(self)
            )
            self.running_state = Runnable.STATE.FAILED_EXECUTION

        self.save()

    def set_running_state(self, quiet=False):
        if can_proceed(self.start_running):
            self.start_running()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            if not quiet:
                Runnable._log.warning(
                    'Forced transition to RUNNING from %s for %s',
                    str(self.running_state),
                    str(self)
                )
                Runnable._log.info(''.join(format_stack()))
            self.running_state = Runnable.STATE.RUNNING
        else:
            self.start_running()  # trigger exception

        self.save()

    def set_success_state(self):
        if can_proceed(self.succeed):
            self.succeed()
        elif self.running_state != Runnable.STATE.FAILED_EXECUTION:
            Runnable._log.warning(
                'Forced transition to SUCCESS from %s for %s',
                str(self.running_state),
                str(self)
            )
            self.running_state = Runnable.STATE.SUCCESS
        else:
            self.succeed()  # trigger exception

        self.save()

    def set_process_killed_state(self):
        if can_proceed(self.kill_process):
            self.kill_process()
        else:
            Runnable._log.warning(
                'Forced transition to PROCESS_KILLED from %s for %s',
                str(self.running_state),
                str(self)
            )
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

