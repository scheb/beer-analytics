from abc import ABC
from typing import Optional

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import METRIC_PRECISION, lowerfence, q1, q3, upperfence
from recipe_db.analytics.recipe import RecipeLevelAnalysis
from recipe_db.analytics.scope import StyleSelection, FermentableSelection, FermentableScope
from recipe_db.analytics.utils import remove_outliers, get_style_names_dict, get_fermentable_names_dict, db_query_fetch_dictlist


class FermentableLevelAnalysis(ABC):
    def __init__(self, scope: FermentableScope) -> None:
        self.scope: FermentableScope = scope


class FermentableAmountRangeAnalysis(FermentableLevelAnalysis):
    def amount_range(self) -> DataFrame:
        fermentable_scope_filter = self.scope.get_filter()

        query = """
                SELECT rf.recipe_id, SUM(rf.amount_percent) AS amount_percent
                FROM recipe_db_recipefermentable AS rf
                WHERE 1 {where}
                GROUP BY rf.recipe_id, rf.kind_id
            """.format(
                where=fermentable_scope_filter.where_statement
            )

        query_parameters = fermentable_scope_filter.where_parameters
        df = pd.read_sql(query, connection, params=query_parameters)
        if len(df) == 0:
            return df

        # Calculate ranges
        agg = [lowerfence, q1, "median", "mean", q3, upperfence]
        aggregated = df.agg({"amount_percent": agg})

        return aggregated


class FermentableMetricHistogram(FermentableLevelAnalysis):
    def metric_histogram(self, metric: str) -> DataFrame:
        precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION["default"]

        fermentable_scope_filter = self.scope.get_filter()
        query = """
                SELECT ROUND({metric}, {precision}) as {metric}
                FROM recipe_db_recipefermentable AS rf
                WHERE 1 {where}
            """.format(
                metric=metric,
                precision=precision,
                where=fermentable_scope_filter.where_statement,
            )

        query_parameters = fermentable_scope_filter.where_parameters
        df = pd.read_sql(query, connection, params=query_parameters)
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
        fermentable_selection: Optional[FermentableSelection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        fermentable_selection = fermentable_selection or FermentableSelection()

        recipe_scope_filter = self.scope.get_filter()
        fermentable_selection_filter = fermentable_selection.get_filter()

        query = """
                SELECT
                    rf.recipe_id,
                    rf.kind_id,
                    SUM(rf.amount_percent) AS amount_percent
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipefermentable AS rf
                    ON r.uid = rf.recipe_id
                WHERE 1 {where1} {where2}
                GROUP BY rf.recipe_id, rf.kind_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where1=recipe_scope_filter.where_statement,
                where2=fermentable_selection_filter.where_statement
            )

        query_params = (recipe_scope_filter.join_parameters
                        + recipe_scope_filter.where_parameters
                        + fermentable_selection_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_params)
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
        style_selection: Optional[StyleSelection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        style_selection = style_selection or StyleSelection()

        recipe_scope_filter = self.scope.get_filter()
        style_selection_filter = style_selection.get_filter()

        query = """
                SELECT
                    rf.recipe_id,
                    ras.style_id,
                    rf.kind_id,
                    SUM(rf.amount_percent) AS amount_percent
                FROM recipe_db_recipe AS r
                {join}
                JOIN recipe_db_recipefermentable AS rf
                    ON r.uid = rf.recipe_id
                JOIN recipe_db_recipe_associated_styles ras
                    ON r.uid = ras.recipe_id
                WHERE 1 {where1} {where2}
                GROUP BY rf.recipe_id, ras.style_id, rf.kind_id
            """.format(
                join=recipe_scope_filter.join_statement,
                where1=recipe_scope_filter.where_statement,
                where2=style_selection_filter.where_statement
            )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters
                            + style_selection_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_parameters)
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


class UnmappedFermentablesAnalysis:
    def get_unmapped(self) -> list:
        query = """
                SELECT
                    COUNT(DISTINCT rf.recipe_id) AS num_recipes,
                    LOWER(rf.kind_raw) As kind
                FROM recipe_db_recipefermentable AS rf
				WHERE rf.kind_id IS NULL
                GROUP BY LOWER(rf.kind_raw)
                ORDER BY num_recipes DESC
                LIMIT 100
            """

        return db_query_fetch_dictlist(query)
