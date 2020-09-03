from typing import Tuple

from django.core.exceptions import ValidationError
from django.db import transaction

from recipe_db.format.parser import FormatParser, ParserResult
from recipe_db.models import Recipe, RecipeHop, RecipeMalt, RecipeYeast


class RecipeImporter:

    @transaction.atomic
    def import_recipe(self, uid: str, result: ParserResult) -> None:
        result.recipe.uid = uid
        self.set_amount_percent(result.malts)
        self.set_amount_percent(result.hops)

        self.validate_and_fix_recipe(result.recipe)
        result.recipe.save()

        result.recipe.recipemalt_set.add(*result.malts, bulk=False)
        for malt in result.malts:
            self.validate_and_fix_malt(malt)
            malt.save()

        result.recipe.recipehop_set.add(*result.hops, bulk=False)
        for hop in result.hops:
            self.validate_and_fix_hop(hop)
            hop.save()

        result.recipe.recipeyeast_set.add(*result.yeasts, bulk=False)
        for yeast in result.yeasts:
            self.validate_and_fix_yeast(yeast)
            yeast.save()

    def set_amount_percent(self, items: list) -> None:
        total_amount = 0
        for item in items:
            if item.amount is not None:
                total_amount += item.amount
        for item in items:
            if item.amount is not None:
                item.amount_percent = item.amount / total_amount * 100

    def validate_and_fix_recipe(self, recipe: Recipe):
        self.unset_bad_data(recipe)

    def validate_and_fix_malt(self, malt: RecipeMalt):
        self.unset_bad_data(malt)

    def validate_and_fix_hop(self, hop: RecipeHop):
        # Remove odd alpha values
        if hop.alpha is not None and hop.alpha > 30:
            if hop.kind_raw is None:
                hop.alpha = None
            elif not ("extract" in hop.kind_raw.lower() or "oil" in hop.kind_raw.lower()):
                hop.alpha = None

        if hop.time is not None and hop.use is not None:
            if hop.use == RecipeHop.DRY_HOP:
                if hop.time > 43200:  # Limit dry hop time to 30 days max
                    hop.time = None
            else:
                if hop.time > 240:
                    hop.time = None  # Limit boil time to 4 hours max

        self.unset_bad_data(hop)

    def validate_and_fix_yeast(self, yeast: RecipeYeast):
        self.unset_bad_data(yeast)

    def unset_bad_data(self, item):
        last_err = None
        for i in range(0, len(item.__dict__.keys())):
            try:
                item.clean_fields()
                return
            except ValidationError as err:
                last_err = err
                for attribute_name in err.message_dict:
                    setattr(item, attribute_name, None)
        if last_err is not None:
            raise last_err



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
                return Recipe.get_uid(uid), False

        result = self.format_parser.parse_recipe(file_path)
        self.importer.import_recipe(uid, result)
        return result.recipe, True
