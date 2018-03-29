from workflow_engine.strategies.execution_strategy \
    import ExecutionStrategy
import traceback
import logging


class WaitStrategy(ExecutionStrategy):
    _log = logging.getLogger(
        'development.strategies.wait_strategy')

    def must_wait(self, enqueued_object):
        return True

    def skip_execution(self, enqueued_object):
        WaitStrategy._log.info('Skip Execution')

        return True

    def run_task(self, task):
        try:
            enqueued_object = WorkflowController.get_enqueued_object(task)

            if self.must_wait(enqueued_object):
                task.set_queued_state()
                task.job.set_queued_state()
            else:
                self.prep_task(task)
                self.finish_task(task)
        except Exception as e:
            task.set_error_message(
                str(e) + ' - ' + str(traceback.format_exc()))
            self.fail_task(task)

    # deprected
    def finish_task(self, task):
        task.finish_task()


from workflow_engine.workflow_controller import WorkflowController
