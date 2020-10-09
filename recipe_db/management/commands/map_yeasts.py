from django.core.management.base import BaseCommand

from recipe_db.etl.mapping import YeastsProcessor, YeastBrandProductIdMapper, YeastBrandProductNameMapper


class Command(BaseCommand):
    help = "Map yeast values"

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='Map all yeasts (again)')

    def handle(self, *args, **options):
        map_all = options['all']
        yeasts_mapper = YeastsProcessor([YeastBrandProductIdMapper(), YeastBrandProductNameMapper()])

        if map_all:
            self.stdout.write("Mapping all yeasts")
            yeasts_mapper.map_all()
        else:
            self.stdout.write("Mapping unmapped yeasts")
            yeasts_mapper.map_unmapped()

        self.stdout.write("Done")
