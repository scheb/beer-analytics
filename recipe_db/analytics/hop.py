from abc import ABC
from typing import Optional

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import METRIC_PRECISION, lowerfence, q1, q3, upperfence
from recipe_db.analytics.recipe import RecipeLevelAnalysis
from recipe_db.analytics.scope import StyleSelection, HopSelection, HopScope
from recipe_db.analytics.utils import remove_outliers, get_style_names_dict, get_hop_names_dict, db_query_fetch_dictlist, db_query_fetch_single
from recipe_db.models import RecipeHop, Tag, IgnoredHop, Hop


class HopLevelAnalysis(ABC):
    def __init__(self, scope: HopScope) -> None:
        self.scope: HopScope = scope


class HopAmountRangeAnalysis(HopLevelAnalysis):
    def amount_range(self) -> DataFrame:
        hop_scope_filter = self.scope.get_filter()

        query = """
                SELECT rh.recipe_id, SUM(rh.amount_percent) AS amount_percent
                FROM recipe_db_recipehop AS rh
                WHERE 1 {where}
                GROUP BY rh.recipe_id, rh.kind_id
            """.format(
                where=hop_scope_filter.where_statement
            )

        query_parameters = hop_scope_filter.where_parameters
        df = pd.read_sql(query, connection, params=query_parameters)
        if len(df) == 0:
            return df

        # Calculate ranges
        agg = [lowerfence, q1, "median", "mean", q3, upperfence]
        aggregated = df.agg({"amount_percent": agg})

        return aggregated


class HopMetricHistogram(HopLevelAnalysis):
    def metric_histogram(self, metric: str) -> DataFrame:
        precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION["default"]

        hop_scope_filter = self.scope.get_filter()
        query = """
                SELECT ROUND({metric}, {precision}) as {metric}
                FROM recipe_db_recipehop AS rh
                WHERE 1 {where}
            """.format(
            metric=metric,
            precision=precision,
            where=hop_scope_filter.where_statement
        )

        query_parameters = hop_scope_filter.where_parameters
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


class HopAmountAnalysis(RecipeLevelAnalysis):
    def per_hop(
        self,
        hop_selection: Optional[HopSelection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        hop_selection = hop_selection or HopSelection()

        recipe_scope_filter = self.scope.get_filter()
        hop_selection_filter = hop_selection.get_filter()

        query = """
            SELECT
                rh.recipe_id,
                rh.kind_id,
                SUM(rh.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            {join}
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            WHERE 1 {where1} {where2}
            GROUP BY rh.recipe_id, rh.kind_id
        """.format(
            join=recipe_scope_filter.join_statement,
            where1=recipe_scope_filter.where_statement,
            where2=hop_selection_filter.where_statement,
        )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters
                            + hop_selection_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_parameters)
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
        style_selection: Optional[StyleSelection] = None,
        num_top: Optional[int] = None,
    ) -> DataFrame:
        style_selection = style_selection or StyleSelection()

        recipe_scope_filter = self.scope.get_filter()
        style_selection_filter = style_selection.get_filter()

        query = """
            SELECT
                rh.recipe_id,
                ras.style_id,
                rh.kind_id,
                SUM(rh.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            {join}
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            JOIN recipe_db_recipe_associated_styles ras
                ON r.uid = ras.recipe_id
            WHERE 1 {where1} {where2}
            GROUP BY rh.recipe_id, ras.style_id, rh.kind_id
        """.format(
            join=recipe_scope_filter.join_statement,
            where1=recipe_scope_filter.where_statement,
            where2=style_selection_filter.where_statement,
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

    def per_use(self, hop_selection: Optional[HopSelection] = None) -> DataFrame:
        hop_selection = hop_selection or HopSelection()

        recipe_scope_filter = self.scope.get_filter()
        hop_selection_filter = hop_selection.get_filter()
        query = """
            SELECT
                rh.recipe_id,
                rh.use AS use_id,
                rh.kind_id,
                SUM(rh.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            {join}
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            WHERE rh.use IS NOT NULL {where1} {where2}
            GROUP BY rh.recipe_id, rh.use, rh.kind_id
        """.format(
            join=recipe_scope_filter.join_statement,
            where1=recipe_scope_filter.where_statement,
            where2=hop_selection_filter.where_statement,
        )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters
                            + hop_selection_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_parameters)
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
    def pairings(self, hop_selection: Optional[Hop] = None) -> DataFrame:
        recipe_scope_filter = self.scope.get_filter()
        query = """
            SELECT
                rh.recipe_id,
                rh.kind_id,
                SUM(rh.amount_percent) AS amount_percent
            FROM recipe_db_recipe AS r
            {join}
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            WHERE rh.amount_percent > 0 {where}
            GROUP BY rh.recipe_id, rh.kind_id
            ORDER BY rh.kind_id ASC
        """.format(
            join=recipe_scope_filter.join_statement,
            where=recipe_scope_filter.where_statement,
        )

        query_parameters = (recipe_scope_filter.join_parameters
                            + recipe_scope_filter.where_parameters)
        df = pd.read_sql(query, connection, params=query_parameters)

        # Create unique pairs per recipe
        pairs = pd.merge(df, df, on="recipe_id", suffixes=("_1", "_2"))
        pairs = pairs[pairs["kind_id_1"] < pairs["kind_id_2"]]
        pairs["pairing"] = pairs["kind_id_1"] + " " + pairs["kind_id_2"]

        # Filter pairs for hops within selection
        if hop_selection is not None:
            pairs = pairs[(pairs["kind_id_1"] == hop_selection.id) | (pairs["kind_id_2"] == hop_selection.id)]

        # Filter only the top pairs
        top_pairings = pairs["pairing"].value_counts()[:12].index.values
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
        aggregated = aggregated.sort_values(by=[("amount_percent", "count"), "pairing", "kind_id"], ascending=[False, True, True])

        # Finally, add hop names
        aggregated["hop"] = aggregated["kind_id"].map(get_hop_names_dict())

        return aggregated


class UnmappedHopsAnalysis:
    def get_unmapped(self) -> list:
        ignored = IgnoredHop.get_ignore_list()
        if len(ignored) == 0:
            ignored.append("-")  # Work around empty array
        placeholders = ', '.join(['%s'] * len(ignored))

        query = """
                SELECT
                    COUNT(DISTINCT rh.recipe_id) AS num_recipes,
                    LOWER(rh.kind_raw) As kind
                FROM recipe_db_recipehop AS rh
				WHERE rh.kind_id IS NULL AND LOWER(rh.kind_raw) NOT IN ({placeholders})
                GROUP BY LOWER(rh.kind_raw)
                HAVING num_recipes >= 5
                ORDER BY num_recipes DESC
                LIMIT 100
            """.format(placeholders=placeholders)

        return db_query_fetch_dictlist(query, ignored)


class HopFlavorAnalysis:
    def get_associated_flavors(self, tag: Tag) -> list:
        query = """
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
            GROUP BY tags2.tag_id
            ORDER BY combinations DESC
            LIMIT 10
        """

        return db_query_fetch_dictlist(query, [tag.id, tag.id])


class HopSearchAnalysis:
    def get_most_searched_hops(self) -> DataFrame:
        max_volume = db_query_fetch_single("SELECT MAX(search_popularity) FROM recipe_db_hop")

        query = """
            SELECT
                hops.name AS hop, hops.search_popularity AS volume
            FROM recipe_db_hop AS hops
            WHERE hops.search_popularity > 0
            ORDER BY hops.search_popularity DESC
            LIMIT 10
        """

        df = pd.read_sql(query, connection)
        df['volume'] = (df['volume'] / max_volume * 100).round()

        return df

