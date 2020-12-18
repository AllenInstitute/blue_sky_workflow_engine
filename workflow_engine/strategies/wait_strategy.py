from workflow_engine.strategies.execution_strategy import (
    ExecutionStrategy
)
#import traceback
import logging


# DEPRECATED
class WaitStrategy(ExecutionStrategy):
    _log = logging.getLogger(
        'workflow_engine.strategies.wait_strategy')

    def must_wait(self, enqueued_object):
        return True

    def skip_execution(self, enqueued_object):
        WaitStrategy._log.info('Skip Execution')

        return True

    def is_wait_strategy(self):
        return True

    def is_execution_strategy(self):
        return False

    # TODO: execution strategy should inherit from wait strategy
    def set_error_message_from_log(self, task):
        pass
