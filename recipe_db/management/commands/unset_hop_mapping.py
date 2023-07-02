from django.core.management.base import BaseCommand

from recipe_db.models import RecipeHop


class Command(BaseCommand):
    help = "Unset mapping for hop"

    def add_arguments(self, parser):
        parser.add_argument("hop", help="Id of the hop to remove")

    def handle(self, *args, **options):
        hop_id = options["hop"]
        query = RecipeHop.objects.filter(kind_id=hop_id)
        self.stdout.write("Unsetting %s hops" % query.count())
        query.update(kind_id=None)
        self.stdout.write("Done")
