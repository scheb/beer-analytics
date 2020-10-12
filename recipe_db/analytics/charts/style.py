from pandas import DataFrame

from recipe_db.analytics.analysis import RecipesCountAnalysis, RecipesPopularityAnalysis, RecipesMetricHistogram, \
    RecipesTrendAnalysis
from recipe_db.analytics.scope import RecipeScope, StyleProjection
from recipe_db.models import Style


class StyleAnalysis:
    def __init__(self, style: Style) -> None:
        self.style = style
        self.scope = RecipeScope()
        self.scope.styles = [style]

    def recipes_per_month(self) -> DataFrame:
        analysis = RecipesCountAnalysis(self.scope)
        return analysis.per_month()

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        projection = StyleProjection()
        projection.styles = list(self.style.get_style_including_sub_styles())
        return analysis.popularity_per_style(projection)

    def metric_histogram(self, metric: str) -> DataFrame:
        analysis = RecipesMetricHistogram(self.scope)
        return analysis.metric_histogram(metric)

    def trending_hops(self) -> DataFrame:
        analysis = RecipesTrendAnalysis(self.scope)
        return analysis.trending_hops()

    def trending_yeasts(self) -> DataFrame:
        analysis = RecipesTrendAnalysis(self.scope)
        return analysis.trending_yeasts()
