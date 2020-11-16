from typing import Iterable

from pandas import DataFrame

from recipe_db.analytics.hop import HopPairingAnalysis, HopAmountAnalysis, HopAmountRangeAnalysis, HopMetricHistogram
from recipe_db.analytics.recipe import RecipesPopularityAnalysis, CommonStylesAnalysis, RecipesTrendAnalysis, \
    RecipesListAnalysis
from recipe_db.analytics.scope import RecipeScope, HopProjection, HopScope
from recipe_db.models import Hop, Recipe, RecipeHop

USE_FILTER_BITTERING = 'bittering'
USE_FILTER_AROMA = 'aroma'
USE_FILTER_DRY_HOP = 'dry-hop'

HOP_FILTER_TO_USES = {
    USE_FILTER_BITTERING: [RecipeHop.MASH, RecipeHop.FIRST_WORT, RecipeHop.BOIL],
    USE_FILTER_AROMA: [RecipeHop.AROMA],
    USE_FILTER_DRY_HOP: [RecipeHop.DRY_HOP],
}


class HopAnalysis:
    def __init__(self, hop: Hop) -> None:
        self.hop = hop

        self.hop_scope = HopScope()
        self.hop_scope.hops = [hop]

        self.recipe_scope = RecipeScope()
        self.recipe_scope.hop_scope = self.hop_scope

        self.hop_projection = HopProjection()
        self.hop_projection.hops = [hop]

    def metric_histogram(self, metric: str) -> DataFrame:
        analysis = HopMetricHistogram(self.hop_scope)
        return analysis.metric_histogram(metric)

    def amount_range(self) -> DataFrame:
        analysis = HopAmountRangeAnalysis(self.hop_scope)
        return analysis.amount_range()

    def usages(self) -> DataFrame:
        return DataFrame(self.hop.use_count)

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        return analysis.popularity_per_hop(self.hop_projection)

    def amount_per_use(self) -> DataFrame:
        analysis = HopAmountAnalysis(RecipeScope())
        return analysis.per_use(self.hop_projection)

    def amount_per_style(self) -> DataFrame:
        analysis = HopAmountAnalysis(self.recipe_scope)
        return analysis.per_style(num_top=20)

    def common_styles_absolute(self) -> DataFrame:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        return analysis.common_styles_absolute(num_top=20)

    def common_styles_relative(self) -> DataFrame:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        return analysis.common_styles_relative(num_top=20)

    def pairings(self) -> DataFrame:
        analysis = HopPairingAnalysis(RecipeScope())
        return analysis.pairings(self.hop_projection)

    def popular_yeasts(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        return analysis.popularity_per_yeast(num_top=5)

    def trending_yeasts(self) -> DataFrame:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        return analysis.trending_yeasts()

    def random_recipes(self, num_recipes: int) -> Iterable[Recipe]:
        analysis = RecipesListAnalysis(self.recipe_scope)
        return analysis.random(num_recipes)
