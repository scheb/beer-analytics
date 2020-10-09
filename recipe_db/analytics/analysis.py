import math
from abc import ABC

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import POPULARITY_MIN_MONTH, METRIC_PRECISION
from recipe_db.analytics.scope import RecipeScope
from recipe_db.analytics.utils import set_multiple_series_start, remove_outliers, get_style_names_dict, filter_trending, \
    get_hop_names_dict


class RecipesAnalysis(ABC):
    def __init__(self, scope: RecipeScope) -> None:
        self.scope = scope


class RecipesCountAnalysis(RecipesAnalysis):
    def per_month(self) -> DataFrame:
        scope_filter = self.scope.get_filter()
        query = '''
                SELECT
                    date(r.created, 'start of month') AS month,
                    count(r.uid) AS total_recipes
                FROM recipe_db_recipe AS r
                WHERE
                    created IS NOT NULL
                    {}
                GROUP BY date(r.created, 'start of month')
                ORDER BY month ASC
            '''.format(scope_filter.where)

        df = pd.read_sql(query, connection, params=scope_filter.parameters)
        df = df.set_index('month')

        return df

    def per_style(self) -> DataFrame:
        scope_filter = self.scope.get_filter()
        query = '''
                SELECT
                    r.style_id,
                    count(r.uid) AS total_recipes
                FROM recipe_db_recipe AS r
                WHERE
                    style_id IS NOT NULL
                    {}
                GROUP BY r.style_id
                ORDER BY r.style_id ASC
            '''.format(scope_filter.where)

        df = pd.read_sql(query, connection, params=scope_filter.parameters)
        df = df.set_index('style_id')

        return df


class RecipesPopularityAnalysis(RecipesAnalysis):
    def __init__(self, scope: RecipeScope) -> None:
        scope.creation_date_min = POPULARITY_MIN_MONTH
        super().__init__(scope)

    def _total_recipes_per_month(self) -> DataFrame:
        return RecipesCountAnalysis(RecipeScope()).per_month()

    def popularity_per_style(self) -> DataFrame:
        scope_filter = self.scope.get_filter()
        query = '''
                SELECT
                    date(r.created, 'start of month') AS month,
                    r.style_id,
                    count(r.uid) AS recipes
                FROM recipe_db_recipe AS r
                WHERE
                    r.created IS NOT NULL
                    {}
                GROUP BY month, r.style_id
            '''.format(scope_filter.where)

        per_month = pd.read_sql(query, connection, params=scope_filter.parameters)
        per_month = per_month.merge(self._total_recipes_per_month(), on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes'] * 100

        per_month = set_multiple_series_start(per_month, 'style_id', 'month', 'recipes_percent')

        per_month['style'] = per_month['style_id'].map(get_style_names_dict())
        return per_month


class RecipesMetricHistogram(RecipesAnalysis):
    def metric_histogram(self, metric: str) -> DataFrame:
        precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION['default']
        scope_filter = self.scope.get_filter()

        query = '''
                SELECT round({}, {}) as {}
                FROM recipe_db_recipe AS r
                WHERE
                    {} IS NOT NULL
                    {}
            '''.format(metric, precision, metric, metric, scope_filter.where)

        df = pd.read_sql(query, connection, params=scope_filter.parameters)
        df = remove_outliers(df, metric, 0.02)

        bins = 16
        if metric in ['og', 'fg'] and len(df) > 0:
            abs = df[metric].max() - df[metric].min()
            bins = max([1, round(abs / 0.002)])
            if bins > 18:
                bins = round(bins / math.ceil(bins / 12))

        histogram = df.groupby([pd.cut(df[metric], bins, precision=precision)])[metric].agg(['count'])
        histogram = histogram.reset_index()
        histogram[metric] = histogram[metric].map(str)

        return histogram


class RecipesTrendAnalysis(RecipesAnalysis):
    def __init__(self, scope: RecipeScope) -> None:
        scope.creation_date_min = POPULARITY_MIN_MONTH
        super().__init__(scope)

    def _recipes_per_month_in_scope(self) -> DataFrame:
        return RecipesCountAnalysis(self.scope).per_month()

    def trending_hops(self) -> DataFrame:
        recipes_per_month = self._recipes_per_month_in_scope()
        scope_filter = self.scope.get_filter()

        query = '''
                SELECT
                    date(r.created, 'start of month') AS month,
                    rh.kind_id,
                    count(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                JOIN recipe_db_recipehop AS rh
                    ON r.uid = rh.recipe_id
                WHERE
                    r.created IS NOT NULL
                    AND rh.kind_id IS NOT NULL
                    {}
                GROUP BY date(r.created, 'start of month'), rh.kind_id
            '''.format(scope_filter.where)

        per_month = pd.read_sql(query, connection, params=scope_filter.parameters)
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['month'] = pd.to_datetime(per_month['month'])
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes'] * 100

        trending = filter_trending(per_month, 'kind_id', 'month', 'recipes_percent')
        trending = set_multiple_series_start(trending, 'kind_id', 'month', 'recipes_percent')

        trending['hop'] = trending['kind_id'].map(get_hop_names_dict())
        return trending

    def trending_yeasts(self) -> DataFrame:
        return DataFrame()


# Helper function used for ingredients analysis
def get_num_recipes_per_month() -> DataFrame:
    return RecipesCountAnalysis(RecipeScope()).per_month()


# Helper function used for ingredients analysis
def get_num_recipes_per_style() -> DataFrame:
    return RecipesCountAnalysis(RecipeScope()).per_style()
