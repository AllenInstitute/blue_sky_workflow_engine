#!/usr/bin/env python
'''
Ingest json message

Send EM tileset data using blue sky's celery ingest call
'''
from workflow_engine.client_settings import configure_worker_app
import celery
from celery import Celery, signature
import sys
import os
import json
import click
import datetime
import pytz
import logging

@celery.signals.after_setup_task_logger.connect
def after_setup_celery_task_logger(logger, **kwargs):
    with open(os.environ['BLUE_SKY_LOGGING_CONFIG'], 'r') as f:
        logging_config = json.load(f)
        logging_config['handlers']['file']['filename'] = os.environ['DEBUG_LOG']
    logging.config.dictConfig(logging_config)

class settings_attr_dict(dict):
    __getattr__ = dict.get

ingest_signature = signature(
    'workflow_engine.process.workers.ingest_tasks.ingest_task')
ingest_signature.set(time_limit=10)

class IngestClient():
    _log = logging.getLogger('workflow_engine.ingest.ingest_client')

    def __init__(self, app_key, workflow_name):
        self.app_key = app_key
        self.workflow_name = workflow_name

    def send(self, body_data, fix_option=[]):
        result = ingest_signature.delay(
            self.workflow_name, body_data, fix_option
        )

        response_message = result.wait(10)

        return response_message


    @classmethod
    def gen_datetime(cls, timestr, tz=None):
        tz = (tz if tz else cls.timezone)
        return pytz.timezone(tz).localize(
            datetime.datetime.strptime(timestr, '%Y%m%d%H%M%S'))

    # FIXME just passthrough right now -- see tim's integration
    @classmethod
    def gen_timestring(cls, timestr, **kwargs):
        return cls.gen_datetime(timestr, **kwargs).isoformat()

    def run(self, input_data, tag = None):
        if tag is None:
            tags = []
        else:
            tags = [ tag ]

        with open(input_data, 'r') as f:
            body = json.load(f)

        response = self.send(body, fix_option=tags)

        IngestClient._log.info("celery ingest returned {}".format(response))
        print("celery ingest returned {}".format(response))
        # TODO return this or have it set in order to facilitate RefSet
        IngestClient._log.info("enqueued object: %s",
            str(response))


    def configure_celery_app(self):
        try:
            del os.environ['DJANGO_SETTINGS_MODULE']
        except:
            pass

        #settings = load_settings_yaml()

        #blue_sky_settings = os.environ['BLUE_SKY_SETTINGS']

        #with open(blue_sky_settings, 'r') as f:
        #    settings = yaml.load(f, Loader=yaml.SafeLoader)

        app = Celery('workflow_engine.celery')
        #blue_sky_settings = settings_attr_dict(settings)
        #app.config_from_object(blue_sky_settings)
        configure_worker_app(app, 'blue_sky')


@click.command()
@click.option('--exchange', default='blue_sky__blue', help="messaging system exchange name")
@click.option('--workflow', default='mock_workflow', help="destination for message")
@click.option('--message_file', default='message.json', help="json file containing message boy")
@click.option('--tag', required=False, help="additional information for ingest strategy")
def main(exchange, workflow, message_file, tag):
    IngestClient._log.info('RUNNING')
    mod = IngestClient(exchange, workflow)
    mod.configure_celery_app()
    mod.run(message_file, tag)

if __name__ == "__main__":
    main()
