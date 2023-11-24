import math
from abc import ABC
from typing import Optional, Iterable

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import METRIC_PRECISION, POPULARITY_START_MONTH, POPULARITY_CUT_OFF_DATE
from recipe_db.analytics.scope import (
    RecipeScope,
    StyleProjection,
    YeastProjection,
    HopProjection,
    FermentableProjection,
)
from recipe_db.analytics.utils import (
    remove_outliers,
    get_style_names_dict,
    get_hop_names_dict,
    get_yeast_names_dict,
    get_fermentable_names_dict,
    RollingAverage,
    Trending,
    months_ago, db_query_fetch_single,
)
from recipe_db.models import Recipe, Style


class RecipeLevelAnalysis(ABC):
    def __init__(self, scope: RecipeScope) -> None:
        self.scope = scope


class RecipesListAnalysis(RecipeLevelAnalysis):
    def random(self, num_recipes: int) -> Iterable[Recipe]:
        recipe_scope_filter = self.scope.get_filter()
        query = """
                SELECT r.uid AS recipe_id
                FROM recipe_db_recipe AS r
                {join}
                WHERE 1 {where}
                ORDER BY RAND()
                LIMIT %s
            """.format(
                join=recipe_scope_filter.join_statement,
                where=recipe_scope_filter.where_statement
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters
                            + [num_recipes])
        df = pd.read_sql(query, connection, params=query_parameters)
        recipe_ids = df["recipe_id"].values.tolist()
        if len(recipe_ids) == 0:
            return []

        return Recipe.objects.filter(uid__in=recipe_ids).order_by("name")


class RecipesCountAnalysis(RecipeLevelAnalysis):
    def total(self) -> int:
        recipe_scope_filter = self.scope.get_filter()
        query = """
                SELECT
                    COUNT(*) AS total_recipes
                FROM recipe_db_recipe AS r
                {join}
                WHERE created IS NOT NULL {where}
            """.format(
                join=recipe_scope_filter.join_statement,
                where=recipe_scope_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters)
        return db_query_fetch_single(query, query_parameters)

    def per_day(self) -> DataFrame:
        recipe_scope_filter = self.scope.get_filter()
        query = """
                SELECT
                    DATE(r.created) AS day,
                    COUNT(*) AS total_recipes
                FROM recipe_db_recipe AS r
                {join}
                WHERE created IS NOT NULL {where}
                GROUP BY date(r.created)
            """.format(
                join=recipe_scope_filter.join_statement,
                where=recipe_scope_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_parameters)
        df = df.set_index("day")

        return df

    def per_month(self) -> DataFrame:
        recipe_scope_filter = self.scope.get_filter()
        query = """
                SELECT
                    DATE_ADD(DATE(r.created), INTERVAL -DAY(r.created)+1 DAY) AS month,
                    COUNT(*) AS total_recipes
                FROM recipe_db_recipe AS r
                {join}
                WHERE created IS NOT NULL {where}
                GROUP BY month
                ORDER BY month ASC
            """.format(
                join=recipe_scope_filter.join_statement,
                where=recipe_scope_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_parameters)
        df = df.set_index("month")

        return df

    def per_style(self) -> DataFrame:
        recipe_scope_filter = self.scope.get_filter()

        # Optimization: No filter criteria given => use pre-calculated values from the styles
        if not recipe_scope_filter.has_filter():
            return self._per_style_total()

        query = """
                SELECT
                    ras.style_id,
                    COUNT(DISTINCT r.uid) AS total_recipes
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipe_associated_styles ras
                    ON r.uid = ras.recipe_id
                WHERE 1 {where}
                GROUP BY ras.style_id
                ORDER BY ras.style_id ASC
            """.format(
                join=recipe_scope_filter.join_statement,
                where=recipe_scope_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_parameters)
        df = df.set_index("style_id")
        return df

    def _per_style_total(self) -> DataFrame:
        query = """
                SELECT
                    s.id AS style_id,
                    s.recipes_count AS total_recipes
                FROM recipe_db_style AS s
            """

        df = pd.read_sql(query, connection)
        df = df.set_index("style_id")
        return df


class RecipesPopularityAnalysis(RecipeLevelAnalysis):
    def popularity_per_style(
        self,
        projection: Optional[StyleProjection] = None,
        num_top: Optional[int] = None,
        top_months: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or StyleProjection()

        recipe_scope_filter = self.scope.get_filter()
        style_projection_filter = projection.get_filter()
        query = """
                SELECT
                    DATE_ADD(DATE(r.created), INTERVAL -DAY(r.created)+1 DAY) AS month,
                    ras.style_id,
                    COUNT(*) AS recipes
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipe_associated_styles AS ras
                    ON r.uid = ras.recipe_id
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    {where1} {where2}
                GROUP BY month, ras.style_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where1=recipe_scope_filter.where_statement,
                where2=style_projection_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + [POPULARITY_CUT_OFF_DATE]
                            + recipe_scope_filter.where_parameters
                            + style_projection_filter.where_parameters)
        per_month = pd.read_sql(query, connection, params=query_parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_scope = per_month
            if top_months is not None:
                top_scope = top_scope[top_scope["month"] >= months_ago(top_months)]
            top_ids = top_scope.groupby("style_id")["recipes"].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month["style_id"].isin(top_ids)]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month["recipes_percent"] = per_month["recipes"] / per_month["total_recipes"]

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(per_month, "style_id", "month")
        smoothened["recipes_percent"] = smoothened["recipes_percent"].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened["month"] >= POPULARITY_START_MONTH]

        # Sort by top styles
        if top_ids is not None:
            remaining_top_ids = set(smoothened["style_id"].unique()) & set(top_ids)
            smoothened["style_id"] = pd.Categorical(smoothened["style_id"], remaining_top_ids)
            smoothened = smoothened.sort_values(["style_id", "month"])

        smoothened["beer_style"] = smoothened["style_id"].map(get_style_names_dict())
        return smoothened

    def popularity_per_hop(
        self,
        projection: Optional[HopProjection] = None,
        num_top: Optional[int] = None,
        top_months: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or HopProjection()

        recipe_scope_filter = self.scope.get_filter()
        hop_projection_filter = projection.get_filter()
        query = """
                SELECT
                    DATE_ADD(DATE(r.created), INTERVAL -DAY(r.created)+1 DAY) AS month,
                    rh.kind_id,
                    COUNT(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipehop AS rh
                    ON r.uid = rh.recipe_id
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    {where1} {where2}
                GROUP BY month, rh.kind_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where1=recipe_scope_filter.where_statement,
                where2=hop_projection_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + [POPULARITY_CUT_OFF_DATE]
                            + recipe_scope_filter.where_parameters
                            + hop_projection_filter.where_parameters)
        per_month = pd.read_sql(query, connection, params=query_parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_scope = per_month
            if top_months is not None:
                top_scope = top_scope[top_scope["month"] >= months_ago(top_months)]
            top_ids = top_scope.groupby("kind_id")["recipes"].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month["kind_id"].isin(top_ids)]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month["recipes_percent"] = per_month["recipes"] / per_month["total_recipes"]

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(per_month, "kind_id", "month")
        smoothened["recipes_percent"] = smoothened["recipes_percent"].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened["month"] >= POPULARITY_START_MONTH]

        # Sort by top kinds
        if top_ids is not None:
            remaining_top_ids = set(smoothened["kind_id"].unique()) & set(top_ids)
            smoothened["kind_id"] = pd.Categorical(smoothened["kind_id"], remaining_top_ids)
            smoothened = smoothened.sort_values(["kind_id", "month"])

        smoothened["hop"] = smoothened["kind_id"].map(get_hop_names_dict())
        return smoothened

    def popularity_per_fermentable(
        self,
        projection: Optional[FermentableProjection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or FermentableProjection()

        recipe_scope_filter = self.scope.get_filter()
        fermentable_projection_filter = projection.get_filter()
        query = """
                SELECT
                    DATE_ADD(DATE(r.created), INTERVAL -DAY(r.created)+1 DAY) AS month,
                    rf.kind_id,
                    COUNT(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipefermentable AS rf
                    ON r.uid = rf.recipe_id
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    {where1} {where2}
                GROUP BY month, rf.kind_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where1=recipe_scope_filter.where_statement,
                where2=fermentable_projection_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + [POPULARITY_CUT_OFF_DATE]
                            + recipe_scope_filter.where_parameters
                            + fermentable_projection_filter.where_parameters)
        per_month = pd.read_sql(query, connection, params=query_parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_scope = per_month
            top_ids = top_scope.groupby("kind_id")["recipes"].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month["kind_id"].isin(top_ids)]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month["recipes_percent"] = per_month["recipes"] / per_month["total_recipes"]

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(per_month, "kind_id", "month")
        smoothened["recipes_percent"] = smoothened["recipes_percent"].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened["month"] >= POPULARITY_START_MONTH]

        # Sort by top kinds
        if top_ids is not None:
            remaining_top_ids = set(smoothened["kind_id"].unique()) & set(top_ids)
            smoothened["kind_id"] = pd.Categorical(smoothened["kind_id"], remaining_top_ids)
            smoothened = smoothened.sort_values(["kind_id", "month"])

        smoothened["fermentable"] = smoothened["kind_id"].map(get_fermentable_names_dict())
        return smoothened

    def popularity_per_yeast(
        self,
        projection: Optional[YeastProjection] = None,
        num_top: Optional[int] = None,
        top_months: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or YeastProjection()

        recipe_scope_filter = self.scope.get_filter()
        yeast_projection_filter = projection.get_filter()
        query = """
                SELECT
                    DATE_ADD(DATE(r.created), INTERVAL -DAY(r.created)+1 DAY) AS month,
                    ry.kind_id,
                    COUNT(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipeyeast AS ry
                    ON r.uid = ry.recipe_id
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    {where1} {where2}
                GROUP BY month, ry.kind_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where1=recipe_scope_filter.where_statement,
                where2=yeast_projection_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + [POPULARITY_CUT_OFF_DATE]
                            + recipe_scope_filter.where_parameters
                            + yeast_projection_filter.where_parameters)
        per_month = pd.read_sql(query, connection, params=query_parameters)
        if len(per_month) == 0:
            return per_month

        # Filter top values
        top_ids = None
        if num_top is not None:
            top_scope = per_month
            if top_months is not None:
                top_scope = top_scope[top_scope["month"] >= months_ago(top_months)]
            top_ids = top_scope.groupby("kind_id")["recipes"].sum().sort_values(ascending=False).index.values[:num_top]
            per_month = per_month[per_month["kind_id"].isin(top_ids)]

        recipes_per_month = RecipesCountAnalysis(self.scope).per_month()
        per_month = per_month.merge(recipes_per_month, on="month")
        per_month["recipes_percent"] = per_month["recipes"] / per_month["total_recipes"]

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(per_month, "kind_id", "month")
        smoothened["recipes_percent"] = smoothened["recipes_percent"].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened["month"] >= POPULARITY_START_MONTH]

        # Sort by top kinds
        if top_ids is not None:
            remaining_top_ids = set(smoothened["kind_id"].unique()) & set(top_ids)
            smoothened["kind_id"] = pd.Categorical(smoothened["kind_id"], remaining_top_ids)
            smoothened = smoothened.sort_values(["kind_id", "month"])

        smoothened["yeast"] = smoothened["kind_id"].map(get_yeast_names_dict())
        return smoothened

    def popularity_per_source(self) -> DataFrame:
        recipe_scope_filter = self.scope.get_filter()
        query = """
                SELECT
                    DATE(r.created) AS day,
                    r.source,
                    COUNT(*) AS recipes_number
                FROM recipe_db_recipe AS r
                {join}
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    {where}
                GROUP BY day, r.source
            """.format(
                join=recipe_scope_filter.join_statement,
                where=recipe_scope_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + [POPULARITY_CUT_OFF_DATE]
                            + recipe_scope_filter.where_parameters)
        per_month = pd.read_sql(query, connection, params=query_parameters)
        return per_month


class RecipesMetricHistogram(RecipeLevelAnalysis):
    def metric_histogram(self, metric: str) -> DataFrame:
        precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION["default"]
        recipe_scope_filter = self.scope.get_filter()

        query = """
                SELECT ROUND({metric}, {precision}) as {metric}
                FROM recipe_db_recipe AS r
                {join}
                WHERE
                    {metric} IS NOT NULL {where}
            """.format(
                metric=metric,
                precision=precision,
                join=recipe_scope_filter.join_statement,
                where=recipe_scope_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_parameters)
        df = remove_outliers(df, metric, 0.02)
        if len(df) == 0:
            return df

        bins = 16
        if metric in ["og", "fg"] and len(df) > 0:
            abs = df[metric].max() - df[metric].min()
            bins = max([1, round(abs / 0.002)])
            if bins > 18:
                bins = round(bins / math.ceil(bins / 12))
        if metric in ["abv", "srm"] and len(df) > 0:
            abs = df[metric].max() - df[metric].min()
            bins = max([1, round(abs / 0.1)])
            if bins > 18:
                bins = round(bins / math.ceil(bins / 12))
        if metric in ["ibu"] and len(df) > 0:
            abs = df[metric].max() - df[metric].min()
            bins = max([1, round(abs)])
            if bins > 18:
                bins = round(bins / math.ceil(bins / 12))

        histogram = df.groupby([pd.cut(df[metric], bins, precision=precision)])[metric].agg(["count"])
        histogram = histogram.reset_index()
        histogram[metric] = histogram[metric].map(str)

        return histogram


class RecipesTrendAnalysis(RecipeLevelAnalysis):
    def _recipes_per_month_in_scope(self) -> DataFrame:
        return RecipesCountAnalysis(self.scope).per_month()

    def trending_styles(self, trend_window_months: int = 24) -> DataFrame:
        recipes_per_month = self._recipes_per_month_in_scope()

        recipe_scope_filter = self.scope.get_filter()
        query = """
                SELECT
                    DATE_ADD(DATE(r.created), INTERVAL -DAY(r.created)+1 DAY) AS month,
                    ras.style_id,
                    COUNT(*) AS recipes
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipe_associated_styles AS ras
                    ON r.uid = ras.recipe_id
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    {where}
                GROUP BY month, ras.style_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where=recipe_scope_filter.where_statement
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + [POPULARITY_CUT_OFF_DATE]
                            + recipe_scope_filter.where_parameters)
        per_month = pd.read_sql(query, connection, params=query_parameters)
        if len(per_month) == 0:
            return per_month

        per_month = per_month.merge(recipes_per_month, on="month")
        per_month["month"] = pd.to_datetime(per_month["month"])
        per_month["recipes_percent"] = per_month["recipes"] / per_month["total_recipes"]

        trend_filter = Trending(RollingAverage(window=trend_window_months + 1), trending_window=trend_window_months)
        trending_ids = trend_filter.get_trending_series(per_month, "style_id", "month", "recipes_percent", "recipes")

        # Filter trending series
        trending = per_month[per_month["style_id"].isin(trending_ids)]
        if len(trending) == 0:
            return trending

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(trending, "style_id", "month")
        smoothened["recipes_percent"] = smoothened["recipes_percent"].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened["month"] >= POPULARITY_START_MONTH]

        # Order by relevance
        remaining_trending_ids = set(smoothened["style_id"].unique()) & set(trending_ids)
        smoothened["style_id"] = pd.Categorical(smoothened["style_id"], remaining_trending_ids)
        smoothened = smoothened.sort_values(["style_id", "month"])

        smoothened["beer_style"] = smoothened["style_id"].map(get_style_names_dict())
        return smoothened

    def trending_hops(self, projection: Optional[HopProjection] = None, trend_window_months: int = 24) -> DataFrame:
        projection = projection or HopProjection()
        recipes_per_month = self._recipes_per_month_in_scope()

        recipe_scope_filter = self.scope.get_filter()
        hop_projection_filter = projection.get_filter()
        query = """
                SELECT
                    DATE_ADD(DATE(r.created), INTERVAL -DAY(r.created)+1 DAY) AS month,
                    rh.kind_id,
                    COUNT(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipehop AS rh
                    ON r.uid = rh.recipe_id
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    AND rh.kind_id IS NOT NULL
                    {where1} {where2}
                GROUP BY month, rh.kind_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where1=recipe_scope_filter.where_statement,
                where2=hop_projection_filter.where_statement
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + [POPULARITY_CUT_OFF_DATE]
                            + recipe_scope_filter.where_parameters
                            + hop_projection_filter.where_parameters)
        per_month = pd.read_sql(query, connection, params=query_parameters)
        if len(per_month) == 0:
            return per_month

        per_month = per_month.merge(recipes_per_month, on="month")
        per_month["month"] = pd.to_datetime(per_month["month"])
        per_month["recipes_percent"] = per_month["recipes"] / per_month["total_recipes"]

        trend_filter = Trending(RollingAverage(window=trend_window_months + 1), trending_window=trend_window_months)
        trending_ids = trend_filter.get_trending_series(per_month, "kind_id", "month", "recipes_percent", "recipes")

        # Filter trending series
        trending = per_month[per_month["kind_id"].isin(trending_ids)]
        if len(trending) == 0:
            return trending

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(trending, "kind_id", "month")
        smoothened["recipes_percent"] = smoothened["recipes_percent"].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened["month"] >= POPULARITY_START_MONTH]

        # Order by relevance
        remaining_trending_ids = set(smoothened["kind_id"].unique()) & set(trending_ids)
        smoothened["kind_id"] = pd.Categorical(smoothened["kind_id"], remaining_trending_ids)
        smoothened = smoothened.sort_values(["kind_id", "month"])

        smoothened["hop"] = smoothened["kind_id"].map(get_hop_names_dict())
        return smoothened

    def trending_yeasts(self, projection: Optional[YeastProjection] = None, trend_window_months: int = 24) -> DataFrame:
        projection = projection or YeastProjection()
        recipes_per_month = self._recipes_per_month_in_scope()

        recipe_scope_filter = self.scope.get_filter()
        yeast_projection_filter = projection.get_filter()
        query = """
                SELECT
                    DATE_ADD(DATE(r.created), INTERVAL -DAY(r.created)+1 DAY) AS month,
                    ry.kind_id,
                    COUNT(DISTINCT r.uid) AS recipes
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipeyeast AS ry
                    ON r.uid = ry.recipe_id
                WHERE
                    r.created >= %s  -- Cut-off date for popularity charts
                    AND ry.kind_id IS NOT NULL
                    {where1} {where2}
                GROUP BY month, ry.kind_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where1=recipe_scope_filter.where_statement,
                where2=yeast_projection_filter.where_statement,
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + [POPULARITY_CUT_OFF_DATE]
                            + recipe_scope_filter.where_parameters
                            + yeast_projection_filter.where_parameters)
        per_month = pd.read_sql(query, connection, params=query_parameters)
        if len(per_month) == 0:
            return per_month

        per_month = per_month.merge(recipes_per_month, on="month")
        per_month["month"] = pd.to_datetime(per_month["month"])
        per_month["recipes_percent"] = per_month["recipes"] / per_month["total_recipes"]

        trend_filter = Trending(RollingAverage(window=trend_window_months + 1), trending_window=trend_window_months)
        trending_ids = trend_filter.get_trending_series(per_month, "kind_id", "month", "recipes_percent", "recipes")

        # Filter trending series
        trending = per_month[per_month["kind_id"].isin(trending_ids)]
        if len(trending) == 0:
            return trending

        # Rolling average
        smoothened = RollingAverage().rolling_multiple_series(trending, "kind_id", "month")
        smoothened["recipes_percent"] = smoothened["recipes_percent"].apply(lambda x: max([x, 0]))

        # Start date for popularity charts
        smoothened = smoothened[smoothened["month"] >= POPULARITY_START_MONTH]

        # Order by relevance
        remaining_trending_ids = set(smoothened["kind_id"].unique()) & set(trending_ids)
        smoothened["kind_id"] = pd.Categorical(smoothened["kind_id"], remaining_trending_ids)
        smoothened = smoothened.sort_values(["kind_id", "month"])

        smoothened["yeast"] = smoothened["kind_id"].map(get_yeast_names_dict())
        return smoothened


class CommonStylesAnalysis(RecipeLevelAnalysis):
    def common_styles_absolute(self, num_top: Optional[int] = None) -> DataFrame:
        df = self._common_styles_data()
        if len(df) == 0:
            return df

        df = df.sort_values("recipes", ascending=False)
        return self._return(df, num_top)

    def common_styles_relative(self, num_top: Optional[int] = None) -> DataFrame:
        df = self._common_styles_data()
        if len(df) == 0:
            return df

        # Calculate percent
        recipes_per_style = RecipesCountAnalysis(RecipeScope()).per_style()
        df = df.merge(recipes_per_style, on="style_id")
        df["recipes_percent"] = df["recipes"] / df["total_recipes"]

        df = df.sort_values("recipes_percent", ascending=False)
        return self._return(df, num_top)

    def _common_styles_data(self) -> DataFrame:
        recipe_scope_filter = self.scope.get_filter()
        query = """
            SELECT
                ras.style_id,
                COUNT(DISTINCT r.uid) AS recipes
            FROM recipe_db_recipe AS r
            {join}
            JOIN recipe_db_recipe_associated_styles AS ras
                ON r.uid = ras.recipe_id
            WHERE 1 {where}
            GROUP BY ras.style_id
        """.format(
            join=recipe_scope_filter.join_statement,
            where=recipe_scope_filter.where_statement,
        )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters)
        return pd.read_sql(query, connection, params=query_parameters)

    def _return(self, df: DataFrame, num_top: Optional[int]) -> DataFrame:
        df["beer_style"] = df["style_id"].map(get_style_names_dict())
        if num_top is not None:
            df = df[:num_top]
        return df
