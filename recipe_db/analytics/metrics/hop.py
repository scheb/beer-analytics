from typing import Tuple

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import lowerfence, upperfence, METRIC_PRECISION
from recipe_db.analytics.utils import remove_outliers
from recipe_db.models import Hop


def load_all_recipe_hops_aggregated():
    df = pd.read_sql_query('SELECT * FROM recipe_db_recipehop', connection)

    # Aggregate per recipe
    df = df.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum", "alpha": "mean", "beta": "mean"}).reset_index()
    df = df.reset_index()

    return df


def calculate_hop_recipe_count(df, hop: Hop) -> int:
    return len(df[df['kind_id'].eq(hop.id)]['recipe_id'].unique())


def calculate_hop_metric(df, hop: Hop, metric: str) -> Tuple[float, float, float]:
    df = df[df['kind_id'].eq(hop.id)]
    return lowerfence(df[metric]), df[metric].median(), upperfence(df[metric])


def get_hop_metric_values(hop: Hop, metric: str) -> DataFrame:
    precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION['default']

    query = '''
            SELECT round({}, {}) as {}
            FROM recipe_db_recipehop
            WHERE kind_id = %s
        '''.format(metric, precision, metric)

    df = pd.read_sql(query, connection, params=[hop.id])
    df = remove_outliers(df, metric, 0.02)

    histogram = df.groupby([pd.cut(df[metric], 16, precision=precision)])[metric].agg(['count'])
    histogram = histogram.reset_index()
    histogram[metric] = histogram[metric].map(str)

    return histogram


def get_hops_percentiles() -> dict:
    df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_hop', connection)
    df['percentile'] = df['recipes_count'].rank(pct=True)
    return df.set_index('id').to_dict('index')
