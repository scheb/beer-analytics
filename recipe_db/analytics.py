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
    df = remove_outliers(df, metric)
    return df[metric].min(), df[metric].mean(), df[metric].max()


def remove_outliers(df, field):
    lower_limit = df[field].quantile(.05)
    upper_limit = df[field].quantile(.95)
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
