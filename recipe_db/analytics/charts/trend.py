from typing import List

from pandas import DataFrame

from recipe_db.analytics.analysis import RecipesPopularityAnalysis
from recipe_db.analytics.scope import RecipeScope, StyleProjection
from recipe_db.models import Style


def get_specific_styles_popularity(styles: List[Style]) -> DataFrame:
    projection = StyleProjection()
    projection.styles = styles
    analysis = RecipesPopularityAnalysis(RecipeScope())
    return analysis.popularity_per_style(projection)
