from django.core.management.base import BaseCommand, CommandError
from workflow_engine.models import Datafix
from django.core.exceptions import ObjectDoesNotExist

class Command(BaseCommand):
    help = 'Run a datafix'

    def add_arguments(self, parser):
        parser.add_argument('name')

    def handle(self, *args, **options):
        name = options['name']
        try:
            try:
                datafix = Datafix.objects.get(name=name)
            except ObjectDoesNotExist:
                datafix = Datafix.create_datafix(name)

            datafix.run()
        except Exception as e:
            print('Something went wrong: ' + str(e))

       