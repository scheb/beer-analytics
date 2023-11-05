from django.db import connection

from recipe_db.analytics.utils import db_query_fetch_dictlist


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
