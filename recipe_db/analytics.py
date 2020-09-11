from typing import Tuple

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.models import Style


def load_all_recipes():
    return pd.read_sql('SELECT * FROM recipe_db_recipe', connection)


def calculate_style_recipe_count(df, style: Style) -> int:
    style_ids = style.get_ids_including_sub_styles()
    return len(df[df['style_id'].isin(style_ids)])


def calculate_style_metric(df, style: Style, metric: str) -> Tuple[float, float, float]:
    style_ids = style.get_ids_including_sub_styles()
    df = df[df['style_id'].isin(style_ids)]
    df = remove_outliers(df, metric, 0.02)
    return df[metric].min(), df[metric].mean(), df[metric].max()


def remove_outliers(df: DataFrame, field: str, cutoff_percentile: float) -> DataFrame:
    lower_limit = df[field].quantile(cutoff_percentile)
    upper_limit = df[field].quantile(1.0 - cutoff_percentile)
    return df[df[field].between(lower_limit, upper_limit)]


def get_style_popularity(style: Style) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()
    df = get_all_styles_popularity()
    df = df.reset_index()
    return df[df['style'].isin(style_ids)]


def get_all_styles_popularity() -> DataFrame:
    query = '''
        SELECT
            strftime('%Y-%m', created) AS month,
            style_id AS style,
            count(uid) AS recipes
        FROM recipe_db_recipe
        WHERE
            created IS NOT NULL
            AND created > '2011-01-01'
            AND style_id IS NOT NULL
        GROUP BY strftime('%Y-%m', created), style_id
    '''

    df = pd.read_sql(query, connection)
    df = df.set_index(['month', 'style'])
    recipes_per_month = df.groupby('month').agg({'recipes': 'sum'})

    return df.div(recipes_per_month, level='month') * 100


def get_style_metric_values(style: Style, metric: str) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()

    query = '''
            SELECT {}
            FROM recipe_db_recipe
            WHERE {} IS NOT NULL AND style_id IN ({})
        '''.format(metric, metric, ','.join('%s' for _ in style_ids))

    df = pd.read_sql(query, connection, params=style_ids)
    df = remove_outliers(df, metric, 0.03)

    df = df.groupby(metric)[metric].agg({'count', 'count'})
    df = df.reset_index()

    return df
