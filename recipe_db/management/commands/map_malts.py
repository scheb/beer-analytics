from django.core.management.base import BaseCommand

from recipe_db.mapping import MaltsMapper


class Command(BaseCommand):
    help = "Map malt values"

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Map all malts (again)')

    def handle(self, *args, **options):
        map_all = options['all']
        malts_mapper = MaltsMapper()

        if map_all:
            self.stdout.write("Mapping all malts")
            malts_mapper.map_all()
        else:
            self.stdout.write("Mapping unmapped malts")
            malts_mapper.map_unmapped()

        self.stdout.write("Done")
