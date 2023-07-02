from django.core.management.base import BaseCommand

from recipe_db.models import Fermentable


class Command(BaseCommand):
    help = "Remove fermentable from database"

    def add_arguments(self, parser):
        parser.add_argument("fermentable", help="Id of the fermentable to remove")

    def handle(self, *args, **options):
        fermentable_id = options["fermentable"]
        Fermentable.objects.filter(id=fermentable_id).delete()
        self.stdout.write("Done")
