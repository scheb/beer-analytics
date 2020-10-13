from pandas import DataFrame

from recipe_db.analytics.fermentable import FermentableAmountAnalysis, FermentableAmountRangeAnalysis, \
    FermentableMetricHistogram
from recipe_db.analytics.recipe import RecipesPopularityAnalysis, CommonStylesAnalysis
from recipe_db.analytics.scope import FermentableScope, RecipeScope, FermentableProjection
from recipe_db.models import Fermentable


class FermentableAnalysis:
    def __init__(self, fermentable: Fermentable) -> None:
        self.fermentable = fermentable

        self.fermentable_scope = FermentableScope()
        self.fermentable_scope.fermentables = [fermentable]

        self.recipe_scope = RecipeScope()
        self.recipe_scope.fermentable_scope = self.fermentable_scope

        self.fermentable_projection = FermentableProjection()
        self.fermentable_projection.fermentables = [fermentable]

    def metric_histogram(self, metric: str) -> DataFrame:
        analysis = FermentableMetricHistogram(self.fermentable_scope)
        return analysis.metric_histogram(metric)

    def amount_range(self) -> DataFrame:
        analysis = FermentableAmountRangeAnalysis(self.fermentable_scope)
        return analysis.amount_range()

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        return analysis.popularity_per_fermentable(self.fermentable_projection)

    def amount_per_style(self) -> DataFrame:
        analysis = FermentableAmountAnalysis(self.recipe_scope)
        return analysis.per_style(num_top=20)

    def common_styles_absolute(self) -> DataFrame:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        return analysis.common_styles_absolute(num_top=20)

    def common_styles_relative(self) -> DataFrame:
        analysis = CommonStylesAnalysis(self.recipe_scope)
        return analysis.common_styles_relative(num_top=20)
