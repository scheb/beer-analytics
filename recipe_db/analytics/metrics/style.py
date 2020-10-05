from typing import Tuple

import pandas as pd
from django.db import connection

from recipe_db.analytics import lowerfence, upperfence
from recipe_db.models import Style


def calculate_style_recipe_count(df, style: Style) -> int:
    style_ids = style.get_ids_including_sub_styles()
    return len(df[df['style_id'].isin(style_ids)])


def calculate_style_metric(df, style: Style, metric: str) -> Tuple[float, float, float]:
    style_ids = style.get_ids_including_sub_styles()
    df = df[df['style_id'].isin(style_ids)]
    return lowerfence(df[metric]), df[metric].median(), upperfence(df[metric])


def get_style_percentiles() -> dict:
    df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_style', connection)
    df['percentile'] = df['recipes_count'].rank(pct=True)
    return df.set_index('id').to_dict('index')

