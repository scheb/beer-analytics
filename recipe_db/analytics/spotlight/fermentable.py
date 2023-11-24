from typing import Iterable

from pandas import DataFrame

from recipe_db.analytics.fermentable import (
    FermentableAmountAnalysis,
    FermentableAmountRangeAnalysis,
    FermentableMetricHistogram,
)
from recipe_db.analytics.recipe import RecipesPopularityAnalysis, CommonStylesAnalysis, RecipesListAnalysis
from recipe_db.analytics.scope import RecipeScope, FermentableSelection, RecipeFermentableScope
from recipe_db.models import Fermentable, Recipe

TYPE_FILTER_BASE = "base"
TYPE_FILTER_CARA_CRYSTAL = "cara-crystal"
TYPE_FILTER_TOASTED = "toasted"
TYPE_FILTER_ROASTED = "roasted"
TYPE_FILTER_OTHER_GRAIN = "other-grain"
TYPE_FILTER_SUGAR = "sugar"
TYPE_FILTER_FRUIT = "fruit"

FERMENTABLE_FILTER_TO_TYPES = {
    TYPE_FILTER_BASE: ([], [Fermentable.BASE]),
    TYPE_FILTER_CARA_CRYSTAL: ([], [Fermentable.CARA_CRYSTAL]),
    TYPE_FILTER_TOASTED: ([], [Fermentable.TOASTED]),
    TYPE_FILTER_ROASTED: ([], [Fermentable.ROASTED]),
    TYPE_FILTER_OTHER_GRAIN: ([], [Fermentable.OTHER_MALT, Fermentable.ADJUNCT, Fermentable.UNMALTED_ADJUNCT]),
    TYPE_FILTER_SUGAR: ([Fermentable.SUGAR], []),
    TYPE_FILTER_FRUIT: ([Fermentable.FRUIT], []),
}


class FermentableAnalysis:
    def __init__(self, fermentable: Fermentable) -> None:
        self.fermentable = fermentable

        self.fermentable_scope = RecipeFermentableScope()
        self.fermentable_scope.fermentables = [fermentable]

        self.recipe_scope = RecipeScope()
        self.recipe_scope.fermentable_scope = self.fermentable_scope

        self.fermentable_selection = FermentableSelection()
        self.fermentable_selection.fermentables = [fermentable]

    def metric_histogram(self, metric: str) -> DataFrame:
        analysis = FermentableMetricHistogram(self.fermentable_scope)
        return analysis.metric_histogram(metric)

    def amount_range(self) -> DataFrame:
        analysis = FermentableAmountRangeAnalysis(self.fermentable_scope)
        return analysis.amount_range()

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        return analysis.popularity_per_fermentable(self.fermentable_selection)

    def amount_per_style(self) -> DataFrame:
        analysis = FermentableAmountAnalysis(self.recipe_scope)
        return analysis.per_style(num_top=20)

    def common_styles_absolute(self) -> DataFrame:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        return analysis.common_styles_absolute(num_top=16)

    def common_styles_relative(self) -> DataFrame:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        return analysis.common_styles_relative(num_top=16)

    def random_recipes(self, num_recipes: int) -> Iterable[Recipe]:
        analysis = RecipesListAnalysis(self.recipe_scope)
        return analysis.random(num_recipes)
