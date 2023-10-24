from django.core.management.base import BaseCommand

from recipe_db.models import Yeast


class Command(BaseCommand):
    help = "Remove yeast from database"

    def add_arguments(self, parser):
        parser.add_argument("yeast", help="Id of the yeast to remove")

    def handle(self, *args, **options):
        yeast_id = options["yeast"]
        Yeast.objects.filter(id=yeast_id).delete()
        self.stdout.write("Done")
