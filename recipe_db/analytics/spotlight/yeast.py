from typing import Iterable

from pandas import DataFrame

from recipe_db.analytics.recipe import (
    RecipesPopularityAnalysis,
    CommonStylesAnalysis,
    RecipesTrendAnalysis,
    RecipesListAnalysis,
)
from recipe_db.analytics.scope import RecipeScope, YeastSelection, RecipeYeastScope
from recipe_db.models import Yeast, Recipe

USE_FILTER_ALE = "ale"
USE_FILTER_LAGER = "lager"
USE_FILTER_WHEAT = "wheat"
USE_FILTER_BRETT_BACTERIA = "brett-bacteria"

YEAST_FILTER_TO_TYPES = {
    USE_FILTER_ALE: [Yeast.ALE],
    USE_FILTER_LAGER: [Yeast.LAGER],
    USE_FILTER_WHEAT: [Yeast.WHEAT],
    USE_FILTER_BRETT_BACTERIA: [Yeast.BRETT_BACTERIA],
}


class YeastAnalysis:
    def __init__(self, yeast: Yeast) -> None:
        self.yeast = yeast

        self.recipe_scope = RecipeScope()
        self.recipe_scope.yeast_scope = RecipeYeastScope()
        self.recipe_scope.yeast_scope.yeasts = [yeast]

        self.yeast_selection = YeastSelection()
        self.yeast_selection.yeasts = [yeast]

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        return analysis.popularity_per_yeast(self.yeast_selection)

    def common_styles_absolute(self) -> DataFrame:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        return analysis.common_styles_absolute(num_top=16)

    def common_styles_relative(self) -> DataFrame:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        return analysis.common_styles_relative(num_top=16)

    def trending_hops(self) -> DataFrame:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        return analysis.trending_hops()

    def popular_hops(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        return analysis.popularity_per_hop(num_top=8)

    def random_recipes(self, num_recipes: int) -> Iterable[Recipe]:
        analysis = RecipesListAnalysis(self.recipe_scope)
        return analysis.random(num_recipes)
