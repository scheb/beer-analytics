import abc
from typing import Tuple, List

from django.core.exceptions import ValidationError
from django.db import transaction

from recipe_db.etl.format.parser import FormatParser, ParserResult
from recipe_db.models import Recipe, RecipeHop, RecipeFermentable, RecipeYeast


class ResultPostProcessor:
    @abc.abstractmethod
    def process(self, result: ParserResult) -> None:
        raise NotImplementedError


class RecipeLoader:
    @transaction.atomic
    def import_recipe(self, uid: str, result: ParserResult) -> None:
        result.recipe.uid = uid
        (source, source_id) = uid.split(":")
        result.recipe.source = source
        result.recipe.source_id = source_id

        self.set_amount_percent(result.fermentables)
        self.set_amount_percent(result.hops)

        self.validate_and_fix_recipe(result.recipe)
        result.recipe.save()

        result.recipe.recipefermentable_set.add(*result.fermentables, bulk=False)
        for fermentable in result.fermentables:
            self.validate_and_fix_fermentable(fermentable)
            fermentable.save()

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
        if total_amount:
            for item in items:
                if item.amount is not None:
                    item.amount_percent = item.amount / total_amount

    def validate_and_fix_recipe(self, recipe: Recipe):
        self.unset_bad_data(recipe)

    def validate_and_fix_fermentable(self, fermentable: RecipeFermentable):
        self.unset_bad_data(fermentable)

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
    def __init__(
        self,
        importer: RecipeLoader,
        format_parsers: List[FormatParser],
        post_processors: List[ResultPostProcessor] = None,
        replace_existing=False,
    ) -> None:
        self.importer = importer
        self.format_parsers = format_parsers
        self.post_processors = post_processors
        self.replace_existing = replace_existing

    def import_recipe_from_file(self, file_paths: List[str], uid: str) -> Tuple[Recipe, bool]:
        # Clear the existing recipe if necessary, otherwise skip
        existing_recipes = Recipe.objects.filter(pk=uid)
        if existing_recipes.count() > 0:
            if self.replace_existing:
                existing_recipes.delete()
            else:
                return Recipe.objects.get(pk=uid), False

        result = ParserResult()
        parsing_steps = zip(file_paths, self.format_parsers)
        for parsing_step in parsing_steps:
            (file_path, parser) = parsing_step
            if file_path is not None:
                parser.parse(result, file_path)

        if self.post_processors is not None:
            for post_processor in self.post_processors:
                post_processor.process(result)

        self.importer.import_recipe(uid, result)
        return result.recipe, True
