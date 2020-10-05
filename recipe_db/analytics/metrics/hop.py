from enum import Enum
from typing import List, Optional, Dict

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import lowerfence, upperfence
from recipe_db.models import Hop


class HopMetric(Enum):
    ALPHA = 'alpha'
    BETA = 'beta'
    AMOUNT_PERCENT = 'amount_percent'


class HopMetricCalculator:
    def __init__(self) -> None:
        self.metrics = None
        self.aggregated: Optional[DataFrame] = None
        self.aggregated_hop: Dict[DataFrame] = {}

    @property
    def available_metrics(self) -> List[HopMetric]:
        return list(HopMetric)

    def _get_recipe_hops(self) -> DataFrame:
        if self.aggregated is None:
            self.aggregated = pd.read_sql('SELECT * FROM recipe_db_recipehop WHERE kind_id IS NOT NULL', connection) \
                .groupby(["recipe_id", "kind_id"]) \
                .agg({"amount_percent": "sum", "alpha": "mean", "beta": "mean"}) \
                .reset_index()
        return self.aggregated

    def _get_hop(self, hop: Hop) -> DataFrame:
        if hop.id not in self.aggregated_hop:
            recipes = self._get_recipe_hops()
            self.aggregated_hop[hop.id] = recipes[recipes['kind_id'].eq(hop.id)]
        return self.aggregated_hop[hop.id]

    def calc_recipes_count(self, hop: Hop) -> int:
        return len(self._get_hop(hop)['recipe_id'].unique())

    def calc_metric(self, hop: Hop, metric: HopMetric):
        recipes = self._get_hop(hop)
        field_name = metric.value
        return lowerfence(recipes[field_name]), recipes[field_name].median(), upperfence(recipes[field_name])

    def calc_hop_use_counts(self, hop: Hop) -> dict:
        results = connection.cursor().execute('''
            SELECT use, count(DISTINCT recipe_id) AS num_recipes
            FROM recipe_db_recipehop
            WHERE kind_id = %s AND use IS NOT NULL
            GROUP BY use
        ''', params=[hop.id])

        count_per_use = {}
        for result in results:
            (use, count) = result
            count_per_use[use] = count

        return count_per_use

    def calc_percentiles(self) -> dict:
        df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_hop', connection)
        df['percentile'] = df['recipes_count'].rank(pct=True)
        return df.set_index('id')['percentile'].to_dict()
