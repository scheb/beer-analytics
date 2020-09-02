from typing import Optional, Tuple

from recipe_db.format.parser import FormatParser, ParserResult
from recipe_db.models import Recipe


class RecipeImporter:
    def import_recipe(self, uid: str, result: ParserResult) -> None:
        self.set_amount_percent(result.malts)
        self.set_amount_percent(result.hops)
        self.validate_and_fix(result)

        recipe = result.recipe
        recipe.uid = uid
        recipe.save()
        recipe.recipemalt_set.add(*result.malts, bulk=False)
        recipe.recipehop_set.add(*result.hops, bulk=False)
        recipe.recipeyeast_set.add(*result.yeasts, bulk=False)

    def validate_and_fix(self, result: ParserResult) -> None:
        pass

    def set_amount_percent(self, items: list) -> None:
        total_amount = 0
        for item in items:
            if item.amount is not None:
                total_amount += item.amount
        for item in items:
            if item.amount is not None:
                item.amount_percent = item.amount / total_amount * 100


class RecipeFileProcessor:
    def __init__(self, importer: RecipeImporter, format_parser: FormatParser, replace_existing=False) -> None:
        self.importer = importer
        self.format_parser = format_parser
        self.replace_existing = replace_existing

    def import_recipe_from_file(self, file_path: str, uid: str) -> Tuple[Recipe, bool]:
        # Clear the existing recipe if necessary, otherwise skip
        if Recipe.exists_uid(uid):
            if self.replace_existing:
                Recipe.delete_uid(uid)
            else:
                return Recipe.objects.get(uid), False

        result = self.format_parser.parse_recipe(file_path)
        self.importer.import_recipe(uid, result)
        return result.recipe, True
