from django.core.management.base import BaseCommand

from recipe_db.etl.format.beersmith import BeerSmithParser
from recipe_db.etl.loader import RecipeFileProcessor, RecipeLoader


class Command(BaseCommand):
    help = "Load a recipe into the database from BeerSmith XML"

    def add_arguments(self, parser):
        parser.add_argument("file_path", help="Data file path")
        parser.add_argument("uid", help="Global uid for the recipe")
        parser.add_argument("--replace", action="store_true", help="Replace existing data")

    def handle(self, *args, **options):
        file_path = options["file_path"]
        uid = options["uid"]
        replace = options["replace"]

        self.stdout.write("Load recipe {} from file {}".format(uid, file_path))

        try:
            processor = RecipeFileProcessor(RecipeLoader(), [BeerSmithParser()], replace_existing=replace)
            processor.import_recipe_from_file([file_path], uid)
        except Exception as e:
            self.stderr.write(str(e))
            return

        self.stdout.write("Imported recipe {}".format(uid))
