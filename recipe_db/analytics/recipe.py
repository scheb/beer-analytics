import math
from abc import ABC
from typing import Optional, Iterable

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import METRIC_PRECISION, POPULARITY_START_MONTH, POPULARITY_CUT_OFF_DATE
from recipe_db.analytics.scope import RecipeScope, StyleProjection, YeastProjection, HopProjection, \
    FermentableProjection
from recipe_db.analytics.utils import remove_outliers, get_style_names_dict, get_hop_names_dict, get_yeast_names_dict, \
    get_fermentable_names_dict, RollingAverage, Trending, months_ago
from recipe_db.models import Recipe


class RecipeLevelAnalysis(ABC):
    def __init__(self, scope: RecipeScope) -> None:
        self.scope = scope


class RecipesListAnalysis(RecipeLevelAnalysis):
    def random(self, num_recipes: int) -> Iterable[Recipe]:
        scope_filter = self.scope.get_filter()
        query = '''
                SELECT r.uid AS recipe_id
                FROM recipe_db_recipe AS r
                WHERE r.name IS NOT NULL {}
                ORDER BY random()
                LIMIT %s
            '''.format(scope_filter.where)

        df = pd.read_sql(query, connection, params=scope_filter.parameters + [num_recipes])
        recipe_ids = df['recipe_id'].values.tolist()
        if len(recipe_ids) == 0:
            return []

        return Recipe.objects.filter(uid__in=recipe_ids).order_by('name')


class RecipesCountAnalysis(RecipeLevelAnalysis):
    def total(self) -> int:
        scope_filter = self.scope.get_filter()
        query = '''
                SELECT
                    count(r.uid) AS total_recipes
                FROM recipe_db_recipe AS r
                WHERE
                    created IS NOT NULL
                    {}
            '''.format(scope_filter.where)

        df = pd.read_sql(query, connection, params=scope_filter.parameters)
        if len(df) == 0:
            return 0

        return df['total_recipes'].values.tolist()[0]

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
        top_months: Optional[int] = None,
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
                    r.created >= %s  -- Cut-off date for popularity charts
                    {}
                    {}
                GROUP BY month, ras.style_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_CUT_OFF_DATE] + scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_scope = per_month
            if top_months is not None:
                top_scope = top_scope[top_scope['month'] >= months_ago(top_months).strftime('%Y-%m-%d')]
            top_ids = top_scope.groupby('style_id')['recipes'].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month['style_id'].isin(top_ids)]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(per_month, 'style_id', 'month')
        smoothened['recipes_percent'] = smoothened['recipes_percent'].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened['month'] >= POPULARITY_START_MONTH]

        # Sort by top styles
        if top_ids is not None:
            smoothened['style_id'] = pd.Categorical(smoothened['style_id'], top_ids)
            smoothened = smoothened.sort_values(['style_id', 'month'])

        smoothened['beer_style'] = smoothened['style_id'].map(get_style_names_dict())
        return smoothened

    def popularity_per_hop(
        self,
        projection: Optional[HopProjection] = None,
        num_top: Optional[int] = None,
        top_months: Optional[int] = None,
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
                    r.created >= %s  -- Cut-off date for popularity charts
                    {}
                    {}
                GROUP BY date(r.created, 'start of month'), rh.kind_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_CUT_OFF_DATE] + scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_scope = per_month
            if top_months is not None:
                top_scope = top_scope[top_scope['month'] >= months_ago(top_months).strftime('%Y-%m-%d')]
            top_ids = top_scope.groupby('kind_id')['recipes'].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month['kind_id'].isin(top_ids)]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(per_month, 'kind_id', 'month')
        smoothened['recipes_percent'] = smoothened['recipes_percent'].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened['month'] >= POPULARITY_START_MONTH]

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
                    r.created >= %s  -- Cut-off date for popularity charts
                    {}
                    {}
                GROUP BY date(r.created, 'start of month'), rf.kind_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_CUT_OFF_DATE] + scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_scope = per_month
            top_ids = top_scope.groupby('kind_id')['recipes'].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month['kind_id'].isin(top_ids)]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(per_month, 'kind_id', 'month')
        smoothened['recipes_percent'] = smoothened['recipes_percent'].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened['month'] >= POPULARITY_START_MONTH]

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
        top_months: Optional[int] = None,
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
                    r.created >= %s  -- Cut-off date for popularity charts
                    {}
                    {}
                GROUP BY date(r.created, 'start of month'), ry.kind_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_CUT_OFF_DATE] + scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_scope = per_month
            if top_months is not None:
                top_scope = top_scope[top_scope['month'] >= months_ago(top_months).strftime('%Y-%m-%d')]
            top_ids = top_scope.groupby('kind_id')['recipes'].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month['kind_id'].isin(top_ids)]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(per_month, 'kind_id', 'month')
        smoothened['recipes_percent'] = smoothened['recipes_percent'].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened['month'] >= POPULARITY_START_MONTH]

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
        if len(df) == 0:
            return df

        bins = 16
        if metric in ['og', 'fg'] and len(df) > 0:
            abs = df[metric].max() - df[metric].min()
            bins = max([1, round(abs / 0.002)])
            if bins > 18:
                bins = round(bins / math.ceil(bins / 12))
        if metric in ['abv', 'srm'] and len(df) > 0:
            abs = df[metric].max() - df[metric].min()
            bins = max([1, round(abs / 0.1)])
            if bins > 18:
                bins = round(bins / math.ceil(bins / 12))
        if metric in ['ibu'] and len(df) > 0:
            abs = df[metric].max() - df[metric].min()
            bins = max([1, round(abs)])
            if bins > 18:
                bins = round(bins / math.ceil(bins / 12))

        histogram = df.groupby([pd.cut(df[metric], bins, precision=precision)])[metric].agg(['count'])
        histogram = histogram.reset_index()
        histogram[metric] = histogram[metric].map(str)

        return histogram


class RecipesTrendAnalysis(RecipeLevelAnalysis):
    def _recipes_per_month_in_scope(self) -> DataFrame:
        return RecipesCountAnalysis(self.scope).per_month()

    def trending_styles(self, trend_window_months: int = 24) -> DataFrame:
        recipes_per_month = self._recipes_per_month_in_scope()

        scope_filter = self.scope.get_filter()
        query = '''
                SELECT
                    date(r.created, 'start of month') AS month,
                    ras.style_id,
                    count(r.uid) AS recipes
                FROM recipe_db_recipe AS r
                JOIN recipe_db_recipe_associated_styles AS ras
                    ON r.uid = ras.recipe_id
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    {}
                GROUP BY month, ras.style_id
            '''.format(scope_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_CUT_OFF_DATE] + scope_filter.parameters)
        if len(per_month) == 0:
            return per_month

        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['month'] = pd.to_datetime(per_month['month'])
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        trend_filter = Trending(RollingAverage(window=trend_window_months + 1), trending_window=trend_window_months)
        trending_ids = trend_filter.get_trending_series(per_month, 'style_id', 'month', 'recipes_percent', 'recipes')

        # Filter trending series
        trending = per_month[per_month['style_id'].isin(trending_ids)]
        if len(trending) == 0:
            return trending

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(trending, 'style_id', 'month')
        smoothened['recipes_percent'] = smoothened['recipes_percent'].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened['month'] >= POPULARITY_START_MONTH]

        # Order by relevance
        smoothened['style_id'] = pd.Categorical(smoothened['style_id'], trending_ids)
        smoothened = smoothened.sort_values(['style_id', 'month'])

        smoothened['beer_style'] = smoothened['style_id'].map(get_style_names_dict())
        return smoothened

    def trending_hops(self, projection: Optional[HopProjection] = None, trend_window_months: int = 24) -> DataFrame:
        projection = projection or HopProjection()
        recipes_per_month = self._recipes_per_month_in_scope()

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
                    r.created >= %s  -- Cut-off date for popularity charts
                    AND rh.kind_id IS NOT NULL
                    {}
                    {}
                GROUP BY date(r.created, 'start of month'), rh.kind_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_CUT_OFF_DATE] + scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['month'] = pd.to_datetime(per_month['month'])
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        trend_filter = Trending(RollingAverage(window=trend_window_months+1), trending_window=trend_window_months)
        trending_ids = trend_filter.get_trending_series(per_month, 'kind_id', 'month', 'recipes_percent', 'recipes')

        # Filter trending series
        trending = per_month[per_month['kind_id'].isin(trending_ids)]
        if len(trending) == 0:
            return trending

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(trending, 'kind_id', 'month')
        smoothened['recipes_percent'] = smoothened['recipes_percent'].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened['month'] >= POPULARITY_START_MONTH]

        # Order by relevance
        smoothened['kind_id'] = pd.Categorical(smoothened['kind_id'], trending_ids)
        smoothened = smoothened.sort_values(['kind_id', 'month'])

        smoothened['hop'] = smoothened['kind_id'].map(get_hop_names_dict())
        return smoothened

    def trending_yeasts(self, projection: Optional[YeastProjection] = None, trend_window_months: int = 24) -> DataFrame:
        projection = projection or YeastProjection()
        recipes_per_month = self._recipes_per_month_in_scope()

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
                    r.created >= %s  -- Cut-off date for popularity charts
                    AND ry.kind_id IS NOT NULL
                    {}
                    {}
                GROUP BY date(r.created, 'start of month'), ry.kind_id
            '''.format(scope_filter.where, projection_filter.where)

        per_month = pd.read_sql(query, connection, params=[POPULARITY_CUT_OFF_DATE] + scope_filter.parameters + projection_filter.parameters)
        if len(per_month) == 0:
            return per_month

        per_month = per_month.merge(recipes_per_month, on="month")
        per_month['month'] = pd.to_datetime(per_month['month'])
        per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes']

        trend_filter = Trending(RollingAverage(window=trend_window_months+1), trending_window=trend_window_months)
        trending_ids = trend_filter.get_trending_series(per_month, 'kind_id', 'month', 'recipes_percent', 'recipes')

        # Filter trending series
        trending = per_month[per_month['kind_id'].isin(trending_ids)]
        if len(trending) == 0:
            return trending

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(trending, 'kind_id', 'month')
        smoothened['recipes_percent'] = smoothened['recipes_percent'].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened['month'] >= POPULARITY_START_MONTH]

        # Order by relevance
        smoothened['kind_id'] = pd.Categorical(smoothened['kind_id'], trending_ids)
        smoothened = smoothened.sort_values(['kind_id', 'month'])

        smoothened['yeast'] = smoothened['kind_id'].map(get_yeast_names_dict())
        return smoothened


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
