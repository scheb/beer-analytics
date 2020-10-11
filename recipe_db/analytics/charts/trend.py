from typing import List

from pandas import DataFrame

from recipe_db.analytics.analysis import RecipesPopularityAnalysis
from recipe_db.analytics.scope import RecipeScope
from recipe_db.models import Style


def get_specific_styles_popularity(styles: List[Style]) -> DataFrame:
    scope = RecipeScope()
    scope.style_ids = styles
    scope.include_sub_styles = False  # Only analyze the styles provided
    analysis = RecipesPopularityAnalysis(scope)
    return analysis.popularity_per_style()
