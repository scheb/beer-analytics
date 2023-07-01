from django.core.management.base import BaseCommand

from recipe_db.models import Hop


class Command(BaseCommand):
    help = "Remove hop from database"

    def add_arguments(self, parser):
        parser.add_argument("hop", help="Id of the hop to remove")

    def handle(self, *args, **options):
        hop_id = options["hop"]
        Hop.objects.filter(id=hop_id).delete()
        self.stdout.write("Done")
