from workflow_engine.strategies.execution_strategy \
    import ExecutionStrategy
import traceback
import logging


class WaitStrategy(ExecutionStrategy):
    _log = logging.getLogger(
        'development.strategies.wait_for_lens_correction')

    def must_wait(self, em_mset):
        return True

    def skip_execution(self, em_mset):
        WaitStrategy._log.info('Skip Execution')
        
        return True

    def run_task(self, task):
        try:
            self.prep_task(task)
            task.save()
            task.clear_error_message()
            #self.run_asynchronous_task(task)
            task.set_queued_state()

            em_mset = task.get_enqueued_object()
            if not self.must_wait(em_mset):
                self.finish_task(task)
        except Exception as e:
            task.set_error_message(
                str(e) + ' - ' + str(traceback.format_exc()))
            self.fail_task(task)

    def finish_task(self, task):
        WaitStrategy._log.info('finish task')
        try:
            task.set_finished_execution_state()

            task.set_success_state()
            task.set_end_run_time()

            task.job.set_success_state()
            task.job.set_end_run_time()
            task.job.enqueue_next_queue()
        except Exception as e:
            WaitStrategy._log.error(
                str(e) + ' - ' + str(traceback.format_exc()))
 
            task.set_error_message(
                str(e) + ' - ' + str(traceback.format_exc()))
            self.fail_task(task)

