from django.core.management.base import BaseCommand

from recipe_db.etl.mapping import StylesProcessor, RecipeNameStyleMapper, StyleMapper, RecipeNameStyleExactMatchMapper


class Command(BaseCommand):
    help = "Map style values"

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Map all style (again)")

    def handle(self, *args, **options):
        map_all = options["all"]
        style_mapper = StylesProcessor([RecipeNameStyleExactMatchMapper(), StyleMapper(), RecipeNameStyleMapper()])

        if map_all:
            self.stdout.write("Mapping all styles")
            style_mapper.map_all()
        else:
            self.stdout.write("Mapping unmapped styles")
            style_mapper.map_unmapped()

        self.stdout.write("Done")
