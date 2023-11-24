from typing import Optional, Iterable

from pandas import DataFrame

from recipe_db.analytics.fermentable import FermentableAmountAnalysis
from recipe_db.analytics.hop import HopPairingAnalysis, HopAmountAnalysis
from recipe_db.analytics.recipe import (
    RecipesCountAnalysis,
    RecipesPopularityAnalysis,
    RecipesMetricHistogram,
    RecipesTrendAnalysis,
    RecipesListAnalysis,
)
from recipe_db.analytics.scope import RecipeScope, StyleSelection, HopSelection, FermentableSelection
from recipe_db.analytics.spotlight.fermentable import FERMENTABLE_FILTER_TO_TYPES
from recipe_db.analytics.spotlight.hop import HOP_FILTER_TO_USES
from recipe_db.models import Style, Recipe


class StyleAnalysis:
    def __init__(self, style: Style) -> None:
        self.style = style

        self.recipe_scope = RecipeScope()
        self.recipe_scope.styles = [style]

    def recipes_per_month(self) -> DataFrame:
        analysis = RecipesCountAnalysis(self.recipe_scope)
        return analysis.per_month()

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        style_selection = StyleSelection()
        style_selection.styles = list(self.style.get_style_including_sub_styles())
        return analysis.popularity_per_style(style_selection)

    def metric_histogram(self, metric: str) -> DataFrame:
        analysis = RecipesMetricHistogram(self.recipe_scope)
        return analysis.metric_histogram(metric)

    def trending_hops(self) -> DataFrame:
        analysis = RecipesTrendAnalysis(self.recipe_scope)
        return analysis.trending_hops()

    def popular_hops(self, use_filter: Optional[str] = None) -> DataFrame:
        hop_selection = HopSelection()
        if use_filter in HOP_FILTER_TO_USES:
            hop_selection.uses = HOP_FILTER_TO_USES[use_filter]
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        return analysis.popularity_per_hop(hop_selection, num_top=8)

    def popular_hops_amount(self, use_filter: Optional[str] = None) -> DataFrame:
        hop_selection = HopSelection()
        if use_filter in HOP_FILTER_TO_USES:
            hop_selection.uses = HOP_FILTER_TO_USES[use_filter]
        analysis = HopAmountAnalysis(self.recipe_scope)
        return analysis.per_hop(hop_selection, num_top=8)

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
        fermentable_selection = FermentableSelection()
        if type_filter in FERMENTABLE_FILTER_TO_TYPES:
            (fermentable_selection.categories, fermentable_selection.types) = FERMENTABLE_FILTER_TO_TYPES[type_filter]
        analysis = RecipesPopularityAnalysis(self.recipe_scope)
        return analysis.popularity_per_fermentable(fermentable_selection, num_top=8)

    def popular_fermentables_amount(self, type_filter: Optional[str] = None) -> DataFrame:
        fermentable_selection = FermentableSelection()
        if type_filter in FERMENTABLE_FILTER_TO_TYPES:
            (fermentable_selection.categories, fermentable_selection.types) = FERMENTABLE_FILTER_TO_TYPES[type_filter]
        analysis = FermentableAmountAnalysis(self.recipe_scope)
        return analysis.per_fermentable(fermentable_selection, num_top=8)

    def random_recipes(self, num_recipes: int) -> Iterable[Recipe]:
        analysis = RecipesListAnalysis(self.recipe_scope)
        return analysis.random(num_recipes)
