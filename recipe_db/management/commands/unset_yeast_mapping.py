from django.core.management.base import BaseCommand

from recipe_db.models import RecipeYeast


class Command(BaseCommand):
    help = "Unset mapping for yeast"

    def add_arguments(self, parser):
        parser.add_argument("yeast", help="Id of the yeast to remove")

    def handle(self, *args, **options):
        yeast_id = options["yeast"]
        query = RecipeYeast.objects.filter(kind_id=yeast_id)
        self.stdout.write("Unsetting %s yeasts" % query.count())
        query.update(kind_id=None)
        self.stdout.write("Done")
