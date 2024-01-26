import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics.utils import db_query_fetch_dictlist, db_query_fetch_single


class UnmappedYeastsAnalysis:
    def get_unmapped(self) -> list:
        query = """
                SELECT
                    COUNT(DISTINCT ry.recipe_id) AS num_recipes,
                    LOWER(ry.kind_raw) As kind
                FROM recipe_db_recipeyeast AS ry
				WHERE ry.kind_id IS NULL
                GROUP BY LOWER(ry.kind_raw)
                ORDER BY num_recipes DESC
                LIMIT 100
            """

        return db_query_fetch_dictlist(query)


class YeastSearchAnalysis:
    def get_most_searched_yeasts(self) -> DataFrame:
        max_volume = db_query_fetch_single("SELECT MAX(search_popularity) FROM recipe_db_yeast")

        query = """
            SELECT
                yeasts.name AS yeast, yeasts.search_popularity AS volume
            FROM recipe_db_yeast AS yeasts
            WHERE yeasts.search_popularity > 0
            ORDER BY yeasts.search_popularity DESC
            LIMIT 10
        """

        df = pd.read_sql(query, connection)
        df['volume'] = (df['volume'] / max_volume * 100).round()

        return df
