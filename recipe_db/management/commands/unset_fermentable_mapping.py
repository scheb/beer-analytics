from django.core.management.base import BaseCommand

from recipe_db.models import RecipeFermentable


class Command(BaseCommand):
    help = "Unset mapping for fermentable"

    def add_arguments(self, parser):
        parser.add_argument("fermentable", help="Id of the fermentable to remove")

    def handle(self, *args, **options):
        fermentable_id = options["fermentable"]
        query = RecipeFermentable.objects.filter(kind_id=fermentable_id)
        self.stdout.write("Unsetting %s fermentables" % query.count())
        query.update(kind_id=None)
        self.stdout.write("Done")
