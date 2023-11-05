import pandas as pd
from django.db import connection

from recipe_db.analytics.utils import db_query_fetch_single
from recipe_db.models import Yeast


class YeastMetricCalculator:
    def __init__(self) -> None:
        self.metrics = None

    def get_recipes_count(self, yeast: Yeast) -> int:
        query = """
            SELECT COUNT(DISTINCT recipe_id)
            FROM recipe_db_recipeyeast
            WHERE kind_id = %s
        """
        return db_query_fetch_single(query, [yeast.id])

    def calc_percentiles(self) -> dict:
        df = pd.read_sql_query("SELECT id, recipes_count FROM recipe_db_yeast", connection)
        df["percentile"] = df["recipes_count"].rank(pct=True)
        return df.set_index("id")["percentile"].to_dict()
