import math
from abc import ABC
from typing import Optional

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import METRIC_PRECISION, POPULARITY_MIN_MONTH
from recipe_db.analytics.scope import RecipeScope, StyleProjection, YeastProjection, HopProjection, \
    FermentableProjection
from recipe_db.analytics.utils import remove_outliers, get_style_names_dict, filter_trending, get_hop_names_dict, \
    get_yeast_names_dict, get_fermentable_names_dict, rolling_multiple_series


class RecipeLevelAnalysis(ABC):
    def __init__(self, scope: RecipeScope) -> None:
        self.scope = scope


class RecipesCountAnalysis(RecipeLevelAnalysis):
    def per_day(self) -> DataFrame:
        scope_filter = self.scope.get_filter()
        query = '''
                SELECT
                    date(r.created) AS day,
                    count(r.uid) AS total_recipes
                FROM recipe_db_recipe AS r
                WHERE
                    created IS NOT NULL
                    {}
                GROUP BY date(r.created)
            '''.format(scope_filter.where)

        df = pd.read_sql(query, connection, params=scope_filter.parameters)
        df = df.set_index('day')

        return df

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
                    ras.style_id,
                    count(DISTINCT r.uid) AS total_recipes
                FROM recipe_db_recipe AS r
                JOIN recipe_db_recipe_associated_styles ras
                    ON r.uid = ras.recipe_id
                WHERE
                    1 {}
                GROUP BY ras.style_id
                ORDER BY ras.style_id ASC
            '''.format(scope_filter.where)

        df = pd.read_sql(query, connection, params=scope_filter.parameters)
        df = df.set_index('style_id')

        return df


class RecipesPopularityAnalysis(RecipeLevelAnalysis):
    def popularity_per_style(
        self,
        projection: Optional[StyleProjection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or StyleProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()
        query = '''
                SELECT
                    date(r.created, 'start of month') AS month,
                    ras.style_id,
                    count(r.uid) AS recipes
                FROM recipe_db_recipe AS r
                JOIN recipe_db_recipe_associated_styles AS ras
                    ON r.uid = ras.recipe_id
                WHERE
                    r.created IS NOT NULL
                    {}
                    {}
                GROUP BY month, ras.style_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_ids = per_month.groupby('style_id')['recipes'].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month['style_id'].isin(top_ids)]

        # Cut-off date for popularity charts
        per_month = per_month[per_month['month'] >= POPULARITY_MIN_MONTH]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = rolling_multiple_series(per_month, 'style_id', 'month')

        # Sort by top kinds
        if top_ids is not None:
            smoothened['kind_id'] = pd.Categorical(smoothened['kind_id'], top_ids)
            smoothened = smoothened.sort_values(['kind_id', 'month'])

        smoothened['beer_style'] = smoothened['style_id'].map(get_style_names_dict())
        return smoothened

    def popularity_per_hop(
        self,
        projection: Optional[HopProjection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or HopProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()
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
                    {}
                    {}
                GROUP BY date(r.created, 'start of month'), rh.kind_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_ids = per_month.groupby('kind_id')['recipes'].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month['kind_id'].isin(top_ids)]

        # Cut-off date for popularity charts
        per_month = per_month[per_month['month'] >= POPULARITY_MIN_MONTH]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = rolling_multiple_series(per_month, 'kind_id', 'month')

        # Sort by top kinds
        if top_ids is not None:
            smoothened['kind_id'] = pd.Categorical(smoothened['kind_id'], top_ids)
            smoothened = smoothened.sort_values(['kind_id', 'month'])

        smoothened['hop'] = smoothened['kind_id'].map(get_hop_names_dict())
        return smoothened

    def popularity_per_fermentable(
        self,
        projection: Optional[FermentableProjection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or FermentableProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()
        query = '''
                SELECT
                    date(r.created, 'start of month') AS month,
                    rf.kind_id,
                    count(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                JOIN recipe_db_recipefermentable AS rf
                    ON r.uid = rf.recipe_id
                WHERE
                    r.created IS NOT NULL
                    {}
                    {}
                GROUP BY date(r.created, 'start of month'), rf.kind_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_ids = per_month.groupby('kind_id')['recipes'].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month['kind_id'].isin(top_ids)]

        # Cut-off date for popularity charts
        per_month = per_month[per_month['month'] >= POPULARITY_MIN_MONTH]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = rolling_multiple_series(per_month, 'kind_id', 'month')

        # Sort by top kinds
        if top_ids is not None:
            smoothened['kind_id'] = pd.Categorical(smoothened['kind_id'], top_ids)
            smoothened = smoothened.sort_values(['kind_id', 'month'])

        smoothened['fermentable'] = smoothened['kind_id'].map(get_fermentable_names_dict())
        return smoothened

    def popularity_per_yeast(
        self,
        projection: Optional[YeastProjection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or YeastProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()
        query = '''
                SELECT
                    date(r.created, 'start of month') AS month,
                    ry.kind_id,
                    count(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                JOIN recipe_db_recipeyeast AS ry
                    ON r.uid = ry.recipe_id
                WHERE
                    r.created IS NOT NULL
                    {}
                    {}
                GROUP BY date(r.created, 'start of month'), ry.kind_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_ids = per_month.groupby('kind_id')['recipes'].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month['kind_id'].isin(top_ids)]

        # Cut-off date for popularity charts
        per_month = per_month[per_month['month'] >= POPULARITY_MIN_MONTH]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = rolling_multiple_series(per_month, 'kind_id', 'month')

        # Sort by top kinds
        if top_ids is not None:
            smoothened['kind_id'] = pd.Categorical(smoothened['kind_id'], top_ids)
            smoothened = smoothened.sort_values(['kind_id', 'month'])

        smoothened['yeast'] = smoothened['kind_id'].map(get_yeast_names_dict())
        return smoothened


class RecipesMetricHistogram(RecipeLevelAnalysis):
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


class RecipesTrendAnalysis(RecipeLevelAnalysis):
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
                    AND r.created >= %s  -- Cut-off date for popularity charts
                    AND rh.kind_id IS NOT NULL
                    {}
                GROUP BY date(r.created, 'start of month'), rh.kind_id
            '''.format(scope_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH] + scope_filter.parameters)
        if len(per_month) == 0:
            return per_month

        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['month'] = pd.to_datetime(per_month['month'])
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = rolling_multiple_series(per_month, 'kind_id', 'month')

        # Filter trending series
        trending = filter_trending(smoothened, 'kind_id', 'month', 'recipes_percent')

        trending['hop'] = trending['kind_id'].map(get_hop_names_dict())
        return trending

    def trending_yeasts(self) -> DataFrame:
        recipes_per_month = self._recipes_per_month_in_scope()
        scope_filter = self.scope.get_filter()

        query = '''
                SELECT
                    date(r.created, 'start of month') AS month,
                    ry.kind_id,
                    count(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                JOIN recipe_db_recipeyeast AS ry
                    ON r.uid = ry.recipe_id
                WHERE
                    r.created IS NOT NULL
                    AND r.created >= %s  -- Cut-off date for popularity charts
                    AND ry.kind_id IS NOT NULL
                    {}
                GROUP BY date(r.created, 'start of month'), ry.kind_id
            '''.format(scope_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH] + scope_filter.parameters)
        if len(per_month) == 0:
            return per_month

        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['month'] = pd.to_datetime(per_month['month'])
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = rolling_multiple_series(per_month, 'kind_id', 'month')

        # Filter trending series
        trending = filter_trending(smoothened, 'kind_id', 'month', 'recipes_percent')

        trending['yeast'] = trending['kind_id'].map(get_yeast_names_dict())
        return trending


class CommonStylesAnalysis(RecipeLevelAnalysis):
    def common_styles_absolute(self, num_top: Optional[int] = None) -> DataFrame:
        df = self._common_styles_data()
        if len(df) == 0:
            return df

        df = df.sort_values('recipes', ascending=False)
        return self._return(df, num_top)

    def common_styles_relative(self, num_top: Optional[int] = None) -> DataFrame:
        df = self._common_styles_data()
        if len(df) == 0:
            return df

        # Calculate percent
        recipes_per_style = RecipesCountAnalysis(RecipeScope()).per_style()
        df = df.merge(recipes_per_style, on="style_id")
        df['recipes_percent'] = df['recipes'] / df['total_recipes']

        df = df.sort_values('recipes_percent', ascending=False)
        return self._return(df, num_top)

    def _common_styles_data(self) -> DataFrame:
        scope_filter = self.scope.get_filter()
        query = '''
            SELECT
                ras.style_id,
                count(DISTINCT r.uid) AS recipes
            FROM recipe_db_recipe AS r
            JOIN recipe_db_recipe_associated_styles AS ras
                ON r.uid = ras.recipe_id
                    AND length(ras.style_id) > 2  -- Quick & dirty to remove top-level categories
            WHERE
                1 {}
            GROUP BY ras.style_id
        '''.format(scope_filter.where)

        return pd.read_sql(query, connection, params=scope_filter.parameters)

    def _return(self, df: DataFrame, num_top: Optional[int]) -> DataFrame:
        df['beer_style'] = df['style_id'].map(get_style_names_dict())
        if num_top is not None:
            df = df[:num_top]
        return df
