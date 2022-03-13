from abc import ABC
from typing import Optional

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import METRIC_PRECISION, lowerfence, q1, q3, upperfence
from recipe_db.analytics.recipe import RecipeLevelAnalysis
from recipe_db.analytics.scope import StyleProjection, FermentableProjection, FermentableScope
from recipe_db.analytics.utils import remove_outliers, get_style_names_dict, get_fermentable_names_dict


class FermentableLevelAnalysis(ABC):
    def __init__(self, scope: FermentableScope) -> None:
        self.scope: FermentableScope = scope


class FermentableAmountRangeAnalysis(FermentableLevelAnalysis):
    def amount_range(self) -> DataFrame:
        scope_filter = self.scope.get_filter()

        query = """
            SELECT rf.recipe_id, sum(rf.amount_percent) AS amount_percent
            FROM recipe_db_recipefermentable AS rf
            WHERE 1 {}
            GROUP BY rf.recipe_id, rf.kind_id
        """.format(
            scope_filter.where
        )

        df = pd.read_sql(query, connection, params=scope_filter.parameters)
        if len(df) == 0:
            return df

        # Calculate ranges
        agg = [lowerfence, q1, "median", "mean", q3, upperfence]
        aggregated = df.agg({"amount_percent": agg})

        return aggregated


class FermentableMetricHistogram(FermentableLevelAnalysis):
    def metric_histogram(self, metric: str) -> DataFrame:
        precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION["default"]

        scope_filter = self.scope.get_filter()
        query = """
                SELECT round({}, {}) as {}
                FROM recipe_db_recipefermentable AS rf
                WHERE 1 {}
            """.format(
            metric, precision, metric, scope_filter.where
        )

        df = pd.read_sql(query, connection, params=scope_filter.parameters)
        if len(df) == 0:
            return df

        df = remove_outliers(df, metric, 0.02)
        if len(df) == 0:
            return df

        histogram = df.groupby([pd.cut(df[metric], 16, precision=precision)])[metric].agg(["count"])
        histogram = histogram.reset_index()
        histogram[metric] = histogram[metric].map(str)

        return histogram


class FermentableAmountAnalysis(RecipeLevelAnalysis):
    def per_fermentable(
        self,
        projection: Optional[FermentableProjection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or FermentableProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()

        query = """
            SELECT
                rf.recipe_id,
                rf.kind_id,
                sum(rf.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            JOIN recipe_db_recipefermentable AS rf
                ON r.uid = rf.recipe_id
            WHERE 1
                {}
                {}
            GROUP BY rf.recipe_id, rf.kind_id
        """.format(
            scope_filter.where, projection_filter.where
        )

        df = pd.read_sql(query, connection, params=scope_filter.parameters + projection_filter.parameters)
        if len(df) == 0:
            return df

        # Calculate range
        agg = [lowerfence, q1, "median", "mean", q3, upperfence]
        per_style = df.groupby("kind_id").agg({"amount_percent": agg, "recipe_id": "nunique"})
        per_style = per_style.reset_index()

        # Sort by number of recipes
        per_style = per_style.sort_values(by=("recipe_id", "nunique"), ascending=False)

        # Show only top values
        if num_top is not None:
            per_style = per_style[:num_top]

        # Add style names
        per_style["fermentable"] = per_style["kind_id"].map(get_fermentable_names_dict())
        return per_style

    def per_style(
        self,
        projection: Optional[StyleProjection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or StyleProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()

        query = """
            SELECT
                rf.recipe_id,
                ras.style_id,
                rf.kind_id,
                sum(rf.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            JOIN recipe_db_recipefermentable AS rf
                ON r.uid = rf.recipe_id
            JOIN recipe_db_recipe_associated_styles ras
                ON r.uid = ras.recipe_id
            WHERE 1
                {}
                {}
            GROUP BY rf.recipe_id, ras.style_id, rf.kind_id
        """.format(
            scope_filter.where, projection_filter.where
        )

        df = pd.read_sql(query, connection, params=scope_filter.parameters + projection_filter.parameters)
        if len(df) == 0:
            return df

        # Calculate range
        agg = [lowerfence, q1, "median", "mean", q3, upperfence]
        per_style = df.groupby("style_id").agg({"amount_percent": agg, "recipe_id": "nunique"})
        per_style = per_style.reset_index()

        # Sort by number of recipes
        per_style = per_style.sort_values(by=("recipe_id", "nunique"), ascending=False)

        # Show only top values
        if num_top is not None:
            per_style = per_style[:num_top]

        # Add style names
        per_style["beer_style"] = per_style["style_id"].map(get_style_names_dict())
        return per_style
