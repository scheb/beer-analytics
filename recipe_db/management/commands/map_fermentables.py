from django.core.management.base import BaseCommand

from recipe_db.mapping import FermentablesProcessor, FermentableMapper


class Command(BaseCommand):
    help = "Map fermentable values"

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Map all fermentables (again)')

    def handle(self, *args, **options):
        map_all = options['all']
        fermentables_mapper = FermentablesProcessor([FermentableMapper()])

        if map_all:
            self.stdout.write("Mapping all fermentables")
            fermentables_mapper.map_all()
        else:
            self.stdout.write("Mapping unmapped fermentables")
            fermentables_mapper.map_unmapped()

        self.stdout.write("Done")
