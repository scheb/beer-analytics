from django.core.management.base import BaseCommand

from recipe_db.models import Tag


class Command(BaseCommand):
    help = "Remove flavor from database"

    def add_arguments(self, parser):
        parser.add_argument("flavor", help="Id of the flavor to remove")

    def handle(self, *args, **options):
        flavor_id = options["flavor"]
        Tag.objects.filter(id=flavor_id).delete()
        self.stdout.write("Done")
