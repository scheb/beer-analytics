from django.core.management.base import BaseCommand

from recipe_db.mapping import HopsMapper


class Command(BaseCommand):
    help = "Map hop values"

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Map all hops (again)')

    def handle(self, *args, **options):
        map_all = options['all']
        hops_mapper = HopsMapper()

        if map_all:
            self.stdout.write("Mapping all hops")
            hops_mapper.map_all()
        else:
            self.stdout.write("Mapping unmapped hops")
            hops_mapper.map_unmapped()

        self.stdout.write("Done")
