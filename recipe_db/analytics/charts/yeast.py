import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import POPULARITY_MIN_MONTH
from recipe_db.analytics.analysis import get_num_recipes_per_month, get_num_recipes_per_style
from recipe_db.analytics.utils import set_series_start
from recipe_db.models import Yeast


def get_yeast_popularity(yeast: Yeast) -> DataFrame:
    recipes_per_month = get_num_recipes_per_month()

    query = '''
        SELECT
            date(r.created, 'start of month') AS month,
            ry.kind_id,
            y.name AS yeast,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipeyeast AS ry
            ON r.uid = ry.recipe_id
        JOIN recipe_db_yeast AS y
            ON ry.kind_id = y.id
        WHERE
            r.created IS NOT NULL
            AND r.created > %s
            AND ry.kind_id = %s
        GROUP BY date(r.created, 'start of month'), ry.kind_id
    '''

    per_month = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH, yeast.id])
    per_month = per_month.merge(recipes_per_month, on="month")
    per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes'] * 100

    per_month = set_series_start(per_month, 'month', 'recipes_percent')

    return per_month


def get_yeast_common_styles_absolute(yeast: Yeast) -> DataFrame:
    df = get_yeast_common_styles_data(yeast)

    df = df.sort_values('recipes', ascending=False)
    df = df[:30]

    return df


def get_yeast_common_styles_relative(yeast: Yeast) -> DataFrame:
    recipes_per_style = get_num_recipes_per_style()
    df = get_yeast_common_styles_data(yeast)

    df = df.set_index(['style_id'])
    df = df.merge(recipes_per_style, on="style_id")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
    df = df.sort_values('recipes_percent', ascending=False)
    df = df[:30]
    df = df.reset_index()

    return df


def get_yeast_common_styles_data(yeast: Yeast) -> DataFrame:
    query = '''
        SELECT
            r.style_id,
            s.name AS style_name,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipeyeast AS ry
            ON r.uid = ry.recipe_id
        JOIN recipe_db_style AS s
            ON r.style_id = s.id
        WHERE
            r.created IS NOT NULL
            AND ry.kind_id = %s
        GROUP BY r.style_id
    '''

    return pd.read_sql(query, connection, params=[yeast.id])
