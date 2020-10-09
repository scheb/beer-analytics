from pandas import DataFrame

from recipe_db.analytics.analysis import RecipesPopularityAnalysis
from recipe_db.analytics.scope import RecipeScope


def get_specific_styles_popularity(styles: list) -> DataFrame:
    scope = RecipeScope()
    scope.style_ids = list(map(lambda x: x.id, styles))
    scope.include_sub_styles = False  # Only analyze the styles provided
    analysis = RecipesPopularityAnalysis(scope)
    return analysis.popularity_per_style()
