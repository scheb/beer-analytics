from enum import Enum
from typing import Optional, Dict, List

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import lowerfence, upperfence
from recipe_db.models import Fermentable


class FermentableMetric(Enum):
    AMOUNT_PERCENT = "amount_percent"
    COLOR_LOVIBOND = "color_lovibond"
    COLOR_EBC = "color_ebc"


class FermentableMetricCalculator:
    def __init__(self) -> None:
        self.metrics = None
        self.aggregated: Optional[DataFrame] = None
        self.aggregated_fermentable: Dict[DataFrame] = {}

    @property
    def available_metrics(self) -> List[FermentableMetric]:
        return list(FermentableMetric)

    def _get_recipe_fermentables(self) -> DataFrame:
        if self.aggregated is None:
            self.aggregated = (
                pd.read_sql("SELECT * FROM recipe_db_recipefermentable WHERE kind_id IS NOT NULL", connection)
                .groupby(["recipe_id", "kind_id"])
                .agg({"amount_percent": "sum", "color_lovibond": "mean", "color_ebc": "mean"})
                .reset_index()
            )
        return self.aggregated

    def _get_fermentable(self, fermentable: Fermentable) -> DataFrame:
        if fermentable.id not in self.aggregated_fermentable:
            recipes = self._get_recipe_fermentables()
            self.aggregated_fermentable[fermentable.id] = recipes[recipes["kind_id"].eq(fermentable.id)]
        return self.aggregated_fermentable[fermentable.id]

    def calc_recipes_count(self, fermentable: Fermentable) -> int:
        return len(self._get_fermentable(fermentable)["recipe_id"].unique())

    def calc_metric(self, fermentable: Fermentable, metric: FermentableMetric):
        recipes = self._get_fermentable(fermentable)
        field_name = metric.value
        return lowerfence(recipes[field_name]), recipes[field_name].median(), upperfence(recipes[field_name])

    def calc_percentiles(self) -> dict:
        df = pd.read_sql_query("SELECT id, recipes_count FROM recipe_db_fermentable", connection)
        df["percentile"] = df["recipes_count"].rank(pct=True)
        return df.set_index("id")["percentile"].to_dict()
