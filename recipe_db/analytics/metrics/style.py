from enum import Enum
from typing import Optional, List, Dict

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import lowerfence, upperfence
from recipe_db.models import Style


class StyleMetric(Enum):
    ABV = "abv"
    IBU = "ibu"
    EBC = "ebc"
    SRM = "srm"
    OG = "og"
    FG = "fg"
    ORIGINAL_PLATO = "original_plato"
    FINAL_PLATO = "final_plato"


class StyleMetricCalculator:
    def __init__(self) -> None:
        self.metrics = None
        self.recipes: Optional[DataFrame] = None
        self.style_recipes: Dict[DataFrame] = {}

    @property
    def available_metrics(self) -> List[StyleMetric]:
        return list(StyleMetric)

    def _get_recipes(self) -> DataFrame:
        if self.recipes is None:
            self.recipes = pd.read_sql("SELECT * FROM recipe_db_recipe WHERE style_id IS NOT NULL", connection)
        return self.recipes

    def _get_style_recipes(self, style: Style) -> DataFrame:
        if style.id not in self.style_recipes:
            recipes = self._get_recipes()
            self.style_recipes[style.id] = recipes[recipes["style_id"].str.startswith(style.id)]
        return self.style_recipes[style.id]

    def calc_recipes_count(self, style: Style) -> int:
        return len(self._get_style_recipes(style))

    def calc_metric(self, style: Style, metric: StyleMetric):
        recipes = self._get_style_recipes(style)
        field_name = metric.value
        return lowerfence(recipes[field_name]), recipes[field_name].median(), upperfence(recipes[field_name])

    def calc_percentiles(self) -> dict:
        df = pd.read_sql_query("SELECT id, recipes_count FROM recipe_db_style", connection)
        df["percentile"] = df["recipes_count"].rank(pct=True)
        return df.set_index("id")["percentile"].to_dict()
