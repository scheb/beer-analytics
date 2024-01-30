import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics.utils import db_query_fetch_single, db_query_fetch_dictlist


class StyleSearchAnalysis:
    def get_most_searched_styles(self) -> DataFrame:
        max_volume = db_query_fetch_single("SELECT MAX(search_popularity) FROM recipe_db_style WHERE parent_style_id IS NOT NULL")

        query = """
            SELECT
                styles.name AS beer_style, styles.search_popularity AS volume
            FROM recipe_db_style AS styles
            WHERE styles.search_popularity > 0 AND styles.parent_style_id IS NOT NULL
            ORDER BY styles.search_popularity DESC
            LIMIT 10
        """

        df = pd.read_sql(query, connection)
        df['volume'] = (df['volume'] / max_volume * 100).round()

        return df


class UnmappedStylesAnalysis:
    def get_unmapped(self) -> list:
        query = """
            SELECT
                COUNT(DISTINCT r.uid) AS num_recipes,
                LOWER(r.style_raw) As style_name
            FROM recipe_db_recipe AS r
            WHERE r.style_id IS NULL AND r.style_oor IS NULL
            GROUP BY LOWER(r.style_raw)
            ORDER BY num_recipes DESC
            LIMIT 100
        """

        return db_query_fetch_dictlist(query)
