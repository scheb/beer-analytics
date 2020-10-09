from pandas import DataFrame

from recipe_db.analytics.analysis import RecipesCountAnalysis, RecipesPopularityAnalysis, RecipesMetricHistogram, \
    RecipesTrendAnalysis
from recipe_db.analytics.scope import RecipeScope
from recipe_db.models import Style


class StyleAnalysis:
    def __init__(self, style: Style) -> None:
        self.style = style
        self.scope = RecipeScope()
        self.scope.style_ids = [style.id]

    def recipes_per_month(self):
        analysis = RecipesCountAnalysis(self.scope)
        return analysis.per_month()

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(self.scope)
        return analysis.popularity_per_style()

    def metric_histogram(self, metric: str) -> DataFrame:
        analysis = RecipesMetricHistogram(self.scope)
        return analysis.metric_histogram(metric)

    def trending_hops(self):
        analysis = RecipesTrendAnalysis(self.scope)
        return analysis.trending_hops()

    def trending_yeasts(self):
        analysis = RecipesTrendAnalysis(self.scope)
        return analysis.trending_yeasts()
