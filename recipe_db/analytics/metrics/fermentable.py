from typing import Tuple

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import lowerfence, upperfence, METRIC_PRECISION
from recipe_db.analytics.utils import remove_outliers
from recipe_db.models import Fermentable


def load_all_recipe_fermentables_aggregated():
    df = pd.read_sql('SELECT * FROM recipe_db_recipefermentable', connection)

    # Aggregate per recipe
    df = df.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum", "color_lovibond": "mean", "color_ebc": "mean"}).reset_index()
    df = df.reset_index()

    return df


def calculate_fermentable_recipe_count(df, fermentable: Fermentable) -> int:
    return len(df[df['kind_id'].eq(fermentable.id)]['recipe_id'].unique())


def calculate_fermentable_metric(df, fermentable: Fermentable, metric: str) -> Tuple[float, float, float]:
    df = df[df['kind_id'].eq(fermentable.id)]
    return lowerfence(df[metric]), df[metric].median(), upperfence(df[metric])


def get_fermentable_metric_values(fermentable: Fermentable, metric: str) -> DataFrame:
    precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION['default']

    query = '''
            SELECT round({}, {}) as {}
            FROM recipe_db_recipefermentable
            WHERE kind_id = %s
        '''.format(metric, precision, metric)

    df = pd.read_sql(query, connection, params=[fermentable.id])
    df = remove_outliers(df, metric, 0.02)

    histogram = df.groupby([pd.cut(df[metric], 16, precision=precision)])[metric].agg(['count'])
    histogram = histogram.reset_index()
    histogram[metric] = histogram[metric].map(str)

    return histogram


def get_fermentables_percentiles() -> dict:
    df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_fermentable', connection)
    df['percentile'] = df['recipes_count'].rank(pct=True)
    return df.set_index('id').to_dict('index')
