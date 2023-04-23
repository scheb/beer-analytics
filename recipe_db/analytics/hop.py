from abc import ABC
from typing import Optional

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import METRIC_PRECISION, lowerfence, q1, q3, upperfence
from recipe_db.analytics.recipe import RecipeLevelAnalysis
from recipe_db.analytics.scope import StyleProjection, HopProjection, HopScope
from recipe_db.analytics.utils import remove_outliers, get_style_names_dict, get_hop_names_dict, dictfetchall
from recipe_db.models import RecipeHop, Tag


class HopLevelAnalysis(ABC):
    def __init__(self, scope: HopScope) -> None:
        self.scope: HopScope = scope


class HopAmountRangeAnalysis(HopLevelAnalysis):
    def amount_range(self) -> DataFrame:
        scope_filter = self.scope.get_filter()

        query = """
            SELECT rh.recipe_id, sum(rh.amount_percent) AS amount_percent
            FROM recipe_db_recipehop AS rh
            WHERE 1 {}
            GROUP BY rh.recipe_id, rh.kind_id
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


class HopMetricHistogram(HopLevelAnalysis):
    def metric_histogram(self, metric: str) -> DataFrame:
        precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION["default"]

        scope_filter = self.scope.get_filter()
        query = """
                SELECT round({}, {}) as {}
                FROM recipe_db_recipehop AS rh
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


class HopAmountAnalysis(RecipeLevelAnalysis):
    def per_hop(
        self,
        projection: Optional[HopProjection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        projection = projection or HopProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()

        query = """
            SELECT
                rh.recipe_id,
                rh.kind_id,
                sum(rh.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            WHERE 1
                {}
                {}
            GROUP BY rh.recipe_id, rh.kind_id
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
        per_style["hop"] = per_style["kind_id"].map(get_hop_names_dict())
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
                rh.recipe_id,
                ras.style_id,
                rh.kind_id,
                sum(rh.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            JOIN recipe_db_recipe_associated_styles ras
                ON r.uid = ras.recipe_id
            WHERE 1
                {}
                {}
            GROUP BY rh.recipe_id, ras.style_id, rh.kind_id
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

    def per_use(self, projection: Optional[HopProjection] = None) -> DataFrame:
        projection = projection or HopProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()
        query = """
            SELECT
                rh.recipe_id,
                rh.use AS use_id,
                rh.kind_id,
                sum(rh.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            WHERE
                rh.use IS NOT NULL
                {}
                {}
            GROUP BY rh.recipe_id, rh.use, rh.kind_id
        """.format(
            scope_filter.where, projection_filter.where
        )

        df = pd.read_sql(query, connection, params=scope_filter.parameters + projection_filter.parameters)
        if len(df) == 0:
            return df

        # Calculate range
        agg = [lowerfence, q1, "median", "mean", q3, upperfence]
        per_use = df.groupby("use_id").agg({"amount_percent": agg})
        per_use = per_use.reset_index()

        # Sort by use (in brewing order)
        per_use["use_id"] = pd.Categorical(
            per_use["use_id"], categories=list(RecipeHop.get_uses().keys()), ordered=True
        )
        per_use = per_use.sort_values(by="use_id")

        # Finally, add use names
        per_use["use"] = per_use["use_id"].map(RecipeHop.get_uses())
        return per_use


class HopPairingAnalysis(RecipeLevelAnalysis):
    def pairings(self, projection: Optional[HopProjection] = None) -> DataFrame:
        projection = projection or HopProjection()

        scope_filter = self.scope.get_filter()
        projection_filter = projection.get_filter()
        query = """
            SELECT
                rh.recipe_id,
                rh.kind_id,
                rh.amount_percent,
                (1 {}) AS in_projection
            FROM recipe_db_recipe AS r
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            WHERE 1 {}
        """.format(
            projection_filter.where, scope_filter.where
        )

        df = pd.read_sql(query, connection, params=projection_filter.parameters + scope_filter.parameters)

        # Aggregate amount per recipe
        df = df.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum", "in_projection": "any"}).reset_index()

        # Create unique pairs per recipe
        pairs = pd.merge(df, df, on="recipe_id", suffixes=("_1", "_2"))
        pairs = pairs[pairs["kind_id_1"] < pairs["kind_id_2"]]
        pairs["pairing"] = pairs["kind_id_1"] + " " + pairs["kind_id_2"]

        # Filter pairs for hops within projection
        pairs = pairs[pairs["in_projection_1"] | pairs["in_projection_2"]]

        # Filter only the top pairs
        top_pairings = pairs["pairing"].value_counts()[:8].index.values
        pairs = pairs[pairs["pairing"].isin(top_pairings)]

        # Merge left and right hop into one dataset
        df1 = pairs[["pairing", "kind_id_1", "amount_percent_1"]]
        df1.columns = ["pairing", "kind_id", "amount_percent"]
        df2 = pairs[["pairing", "kind_id_2", "amount_percent_2"]]
        df2.columns = ["pairing", "kind_id", "amount_percent"]
        top_pairings = pd.concat([df1, df2])

        # Calculate boxplot values
        agg = [lowerfence, q1, "median", "mean", q3, upperfence, "count"]
        aggregated = top_pairings.groupby(["pairing", "kind_id"]).agg({"amount_percent": agg})
        aggregated = aggregated.reset_index()
        aggregated = aggregated.sort_values(by=("amount_percent", "count"), ascending=False)

        # Finally, add hop names
        aggregated["hop"] = aggregated["kind_id"].map(get_hop_names_dict())

        return aggregated

class UnmappedHopsAnalysis:
    def get_unmapped(self) -> list:
        query = """
                SELECT
                    COUNT(DISTINCT rh.recipe_id) AS num_recipes,
                    LOWER(rh.kind_raw) As kind
                FROM recipe_db_recipehop AS rh
				WHERE rh.kind_id IS NULL
                GROUP BY LOWER(rh.kind_raw)
                ORDER BY num_recipes DESC
                LIMIT 100
            """

        with connection.cursor() as cursor:
            cursor.execute(query)
            return dictfetchall(cursor)


class HopFlavorAnalysis:
    def get_associated_flavors(self, tag: Tag) -> list:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    tag.*, COUNT(tags2.id) AS combinations
                    FROM recipe_db_hop_aroma_tags AS tags1
                    LEFT JOIN recipe_db_hop AS hops
                        ON tags1.hop_id = hops.id
                    LEFT JOIN recipe_db_hop_aroma_tags AS tags2
                        ON hops.id = tags2.hop_id
                    JOIN recipe_db_tag AS tag
                        ON tags2.tag_id = tag.id
                    WHERE tags1.tag_id = %s AND tags2.tag_id != %s
                    GROUP BY tags2."tag_id"
                    ORDER BY combinations DESC
                    LIMIT 10
            """, [tag.id, tag.id])
            return dictfetchall(cursor)
