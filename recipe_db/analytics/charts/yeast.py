from pandas import DataFrame

from recipe_db.analytics.analysis import RecipesPopularityAnalysis, CommonStylesAnalysis
from recipe_db.analytics.scope import RecipeScope, YeastProjection, YeastScope
from recipe_db.models import Yeast


class YeastAnalysis:
    def __init__(self, yeast: Yeast) -> None:
        self.yeast = yeast

        self.scope = RecipeScope()
        self.scope.yeast_scope = YeastScope()
        self.scope.yeast_scope.yeasts = [yeast]

        self.projection = YeastProjection()
        self.projection.yeasts = [yeast]

    def popularity(self) -> DataFrame:
        analysis = RecipesPopularityAnalysis(RecipeScope())
        return analysis.popularity_per_yeast(self.projection)

    def common_styles_absolute(self):
        analysis = CommonStylesAnalysis(self.scope)
        return analysis.common_styles_absolute()

    def common_styles_relative(self):
        analysis = CommonStylesAnalysis(self.scope)
        return analysis.common_styles_relative()
