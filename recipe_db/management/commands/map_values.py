from django.core.management.base import BaseCommand

from recipe_db.mapping import map_hops


class Command(BaseCommand):
    help = "Map values"

    def handle(self, *args, **options):
        map_hops()
