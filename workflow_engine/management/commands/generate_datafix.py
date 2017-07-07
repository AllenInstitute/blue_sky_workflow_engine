from django.core.management.base import BaseCommand, CommandError
from workflow_engine.models import Datafix
import time

class Command(BaseCommand):
    help = 'Creates a datafix'

    def add_arguments(self, parser):
        parser.add_argument('name')

        parser.add_argument(
            '-w',
            default=False,
            dest='-w',
            help='create datafix in workflow_engine',
            required=False,
            action='store_true'
        )

    def handle(self, *args, **options):
        name = options['name']
        timestamp = str(time.time()).replace('.', '')
        use_workflow_engine = False

        if options['-w']:
            use_workflow_engine = True
            
        full_name = str(name) + '_' + timestamp

        datafix = Datafix(name=full_name, timestamp=timestamp)
        datafix.save()
        datafix.create_file(use_workflow_engine)

        