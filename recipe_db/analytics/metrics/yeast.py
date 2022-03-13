import pandas as pd
from django.db import connection

from recipe_db.models import Yeast


class YeastMetricCalculator:
    def __init__(self) -> None:
        self.metrics = None

    def get_recipes_count(self, yeast: Yeast) -> int:
        query = """
            SELECT count(DISTINCT recipe_id)
            FROM recipe_db_recipeyeast
            WHERE kind_id = %s
        """
        results = connection.cursor().execute(query, params=[yeast.id])
        return next(results)[0]

    def calc_percentiles(self) -> dict:
        df = pd.read_sql_query("SELECT id, recipes_count FROM recipe_db_yeast", connection)
        df["percentile"] = df["recipes_count"].rank(pct=True)
        return df.set_index("id")["percentile"].to_dict()
