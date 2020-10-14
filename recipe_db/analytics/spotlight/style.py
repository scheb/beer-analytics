from typing import Optional

from pandas import DataFrame

from recipe_db.analytics.fermentable import FermentableAmountAnalysis
from recipe_db.analytics.hop import HopPairingAnalysis, HopAmountAnalysis
from recipe_db.analytics.recipe import RecipesCountAnalysis, RecipesPopularityAnalysis, RecipesMetricHistogram, \
    RecipesTrendAnalysis
from recipe_db.analytics.scope import RecipeScope, StyleProjection, HopProjection, FermentableProjection
from recipe_db.models import Style, RecipeHop, Fermentable


class StyleAnalysis:
    USE_FILTER_BITTERING = 'bittering'
    USE_FILTER_AROMA = 'aroma'
    USE_FILTER_DRY_HOP = 'dry-hop'

    TYPE_FILTER_BASE = 'base'
    TYPE_FILTER_CARA_CRYSTAL = 'cara-crystal'
    TYPE_FILTER_TOASTED = 'toasted'
    TYPE_FILTER_ROASTED = 'roasted'
    TYPE_FILTER_OTHER_GRAIN = 'other-grain'
    TYPE_FILTER_SUGAR = 'sugar'
    TYPE_FILTER_FRUIT = 'fruit'

    HOP_FILTER_TO_USES = {
        USE_FILTER_BITTERING: [RecipeHop.MASH, RecipeHop.FIRST_WORT, RecipeHop.BOIL],
        USE_FILTER_AROMA: [RecipeHop.AROMA],
        USE_FILTER_DRY_HOP: [RecipeHop.DRY_HOP],
    }

    FERMENTABLE_FILTER_TO_TYPES = {
        TYPE_FILTER_BASE: ([], [Fermentable.BASE]),
        TYPE_FILTER_CARA_CRYSTAL: ([], [Fermentable.CARA_CRYSTAL]),
        TYPE_FILTER_TOASTED: ([], [Fermentable.TOASTED]),
        TYPE_FILTER_ROASTED: ([], [Fermentable.ROASTED]),
        TYPE_FILTER_OTHER_GRAIN: ([], [Fermentable.OTHER_MALT, Fermentable.ADJUNCT, Fermentable.UNMALTED_ADJUNCT]),
        TYPE_FILTER_SUGAR: ([Fermentable.SUGAR], []),
        TYPE_FILTER_FRUIT: ([Fermentable.FRUIT], []),
    }

    def __init__(self, style: Style) -> None:
        self.style = style

        self.recipe_scope = RecipeScope()
        self.recipe_scope.styles = [style]

    def recipes_per_month(self) -> DataFrame:
        analysis = RecipesCountAnalysis(self.recipe_scope)
        return analysis.per_month()

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        projection = StyleProjection()
        projection.styles = list(self.style.get_style_including_sub_styles())
        return analysis.popularity_per_style(projection)

    def metric_histogram(self, metric: str) -> DataFrame:
        analysis = RecipesMetricHistogram(self.recipe_scope)
        return analysis.metric_histogram(metric)

    def trending_hops(self) -> DataFrame:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        return analysis.trending_hops()

    def popular_hops(self, use_filter: Optional[str] = None) -> DataFrame:
        projection = HopProjection()
        if use_filter in self.HOP_FILTER_TO_USES:
            projection.uses = self.HOP_FILTER_TO_USES[use_filter]
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        return analysis.popularity_per_hop(projection, num_top=8)

    def popular_hops_amount(self, use_filter: Optional[str] = None) -> DataFrame:
        projection = HopProjection()
        if use_filter in self.HOP_FILTER_TO_USES:
            projection.uses = self.HOP_FILTER_TO_USES[use_filter]
        analysis = HopAmountAnalysis(self.recipe_scope)
        return analysis.per_hop(projection, num_top=8)

    def hop_pairings(self) -> DataFrame:
        analysis = HopPairingAnalysis(self.recipe_scope)
        return analysis.pairings()

    def popular_yeasts(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        return analysis.popularity_per_yeast(num_top=5)

    def trending_yeasts(self) -> DataFrame:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        return analysis.trending_yeasts()

    def popular_fermentables(self, type_filter: Optional[str] = None) -> DataFrame:
        projection = FermentableProjection()
        if type_filter in self.FERMENTABLE_FILTER_TO_TYPES:
            (projection.categories, projection.types) = self.FERMENTABLE_FILTER_TO_TYPES[type_filter]
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        return analysis.popularity_per_fermentable(projection, num_top=8)

    def popular_fermentables_amount(self, type_filter: Optional[str] = None) -> DataFrame:
        projection = FermentableProjection()
        if type_filter in self.FERMENTABLE_FILTER_TO_TYPES:
            (projection.categories, projection.types) = self.FERMENTABLE_FILTER_TO_TYPES[type_filter]
        analysis = FermentableAmountAnalysis(self.recipe_scope)
        return analysis.per_fermentable(projection, num_top=8)
