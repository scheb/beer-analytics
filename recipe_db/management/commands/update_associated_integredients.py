from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Update the associated_* tables for ingredients"

    def add_arguments(self, parser):
        parser.add_argument("--entities", "-e", nargs="+", type=str, help="Entities to recalculate")

    def handle(self, *args, **options) -> None:
        entities = options["entities"] or ["hop", "fermentable", "yeast"]
        if "hop" in entities:
            self.calculate_for_hop()
        if "fermentable" in entities:
            self.calculate_for_fermentable()
        if "yeast" in entities:
            self.calculate_for_yeast()

    def calculate_for_hop(self):
        self.stdout.write("Calculate associated hops")
        with connection.cursor() as cursor:
            # Cleanup
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_hops_old")
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_hops_new")

            # Recreate
            cursor.execute("CREATE TABLE recipe_db_recipe_associated_hops_new LIKE recipe_db_recipe_associated_hops")
            cursor.execute("""
                INSERT INTO recipe_db_recipe_associated_hops_new (recipe_id, hop_id)
                SELECT DISTINCT recipe_id, kind_id
                FROM recipe_db_recipehop
                WHERE kind_id IS NOT NULL
            """)
            cursor.execute("""
                RENAME TABLE
                    recipe_db_recipe_associated_hops TO recipe_db_recipe_associated_hops_old,
                    recipe_db_recipe_associated_hops_new TO recipe_db_recipe_associated_hops
            """)
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_hops_old")

    def calculate_for_fermentable(self):
        self.stdout.write("Calculate associated fermentables")
        with connection.cursor() as cursor:
            # Cleanup
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_fermentables_old")
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_fermentables_new")

            # Recreate
            cursor.execute("CREATE TABLE recipe_db_recipe_associated_fermentables_new LIKE recipe_db_recipe_associated_fermentables")
            cursor.execute("""
                INSERT INTO recipe_db_recipe_associated_fermentables_new (recipe_id, fermentable_id)
                SELECT DISTINCT recipe_id, kind_id
                FROM recipe_db_recipefermentable
                WHERE kind_id IS NOT NULL
            """)
            cursor.execute("""
                RENAME TABLE
                    recipe_db_recipe_associated_fermentables TO recipe_db_recipe_associated_fermentables_old,
                    recipe_db_recipe_associated_fermentables_new TO recipe_db_recipe_associated_fermentables
            """)
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_fermentables_old")

    def calculate_for_yeast(self):
        self.stdout.write("Calculate associated yeasts")
        with connection.cursor() as cursor:
            # Cleanup
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_yeasts_old")
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_yeasts_new")

            # Recreate
            cursor.execute("CREATE TABLE recipe_db_recipe_associated_yeasts_new LIKE recipe_db_recipe_associated_yeasts")
            cursor.execute("""
                INSERT INTO recipe_db_recipe_associated_yeasts_new (recipe_id, yeast_id)
                SELECT DISTINCT recipe_id, kind_id
                FROM recipe_db_recipeyeast
                WHERE kind_id IS NOT NULL
            """)
            cursor.execute("""
                RENAME TABLE
                    recipe_db_recipe_associated_yeasts TO recipe_db_recipe_associated_yeasts_old,
                    recipe_db_recipe_associated_yeasts_new TO recipe_db_recipe_associated_yeasts
            """)
            cursor.execute("DROP TABLE IF EXISTS recipe_db_recipe_associated_yeasts_old")
