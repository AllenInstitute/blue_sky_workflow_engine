from django.core.management.base import BaseCommand, CommandError
from workflow_engine.models import Datafix

class Command(BaseCommand):
    help = 'Run all datafixes'

    def handle(self, *args, **options):
        print('running datafixes...')

        Datafix.create_datafix_records_if_needed()

        datafixes = Datafix.objects.filter(run_at=None).order_by('timestamp')
        for datafix in datafixes:
            datafix.run()

        print('Successfully ran ' + str(len(datafixes)) + ' datafixes')