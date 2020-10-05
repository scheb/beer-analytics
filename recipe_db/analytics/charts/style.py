import math

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import POPULARITY_MIN_MONTH, METRIC_PRECISION
from recipe_db.analytics.utils import set_multiple_series_start, remove_outliers, filter_trending, get_hop_names_dict, \
    get_num_recipes_per_month
from recipe_db.models import Style


def get_style_num_recipes_per_month(style_ids: list):
    query = '''
        SELECT date(created, 'start of month') AS month, count(uid) AS total_recipes
        FROM recipe_db_recipe
        WHERE
            created IS NOT NULL
            AND style_id IN ({})
        GROUP BY date(created, 'start of month')
        ORDER BY month ASC
    '''.format(','.join('%s' for _ in style_ids))

    df = pd.read_sql(query, connection, params=style_ids)
    df = df.set_index('month')

    return df


def get_num_recipes_per_style() -> DataFrame:
    query = '''
        SELECT style_id, count(uid) AS total_recipes
        FROM recipe_db_recipe
        WHERE style_id IS NOT NULL
        GROUP BY style_id
        ORDER BY style_id ASC
    '''

    df = pd.read_sql(query, connection)
    df = df.set_index('style_id')

    return df


def get_style_popularity(style: Style) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()
    return calculate_styles_popularity(style_ids)


def get_styles_popularity(styles: list) -> DataFrame:
    style_ids = list(map(lambda x: x.id, styles))
    return calculate_styles_popularity(style_ids)


def calculate_styles_popularity(style_ids: list) -> DataFrame:
    recipes_per_month = get_num_recipes_per_month()

    query = '''
            SELECT
                date(r.created, 'start of month') AS month,
                r.style_id,
                s.name AS style,
                count(r.uid) AS recipes
            FROM recipe_db_recipe AS r
            JOIN recipe_db_style AS s
                ON r.style_id = s.id
            WHERE
                r.created IS NOT NULL
                AND r.created > %s
                AND r.style_id IN ({})
            GROUP BY date(r.created, 'start of month'), r.style_id
        '''.format(','.join('%s' for _ in style_ids))

    per_month = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH] + style_ids)
    per_month = per_month.merge(recipes_per_month, on="month")
    per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes'] * 100

    per_month = set_multiple_series_start(per_month, 'style_id', 'month', 'recipes_percent')

    return per_month


def get_style_metric_values(style: Style, metric: str) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()
    precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION['default']

    query = '''
            SELECT round({}, {}) as {}
            FROM recipe_db_recipe
            WHERE {} IS NOT NULL AND style_id IN ({})
        '''.format(metric, precision, metric, metric, ','.join('%s' for _ in style_ids))

    df = pd.read_sql(query, connection, params=style_ids)
    df = remove_outliers(df, metric, 0.02)

    bins = 16
    if metric in ['og', 'fg'] and len(df) > 0:
        abs = df[metric].max() - df[metric].min()
        bins = max([1, round(abs / 0.002)])
        if bins > 18:
            bins = round(bins / math.ceil(bins / 12))

    histogram = df.groupby([pd.cut(df[metric], bins, precision=precision)])[metric].agg(['count'])
    histogram = histogram.reset_index()
    histogram[metric] = histogram[metric].map(str)

    return histogram


def get_style_trending_hops(style: Style) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()
    recipes_per_month = get_style_num_recipes_per_month(style_ids)

    query = '''
            SELECT
                date(r.created, 'start of month') AS month,
                rh.kind_id,
                count(DISTINCT r.uid) AS recipes
            FROM recipe_db_recipe AS r
            JOIN recipe_db_recipehop AS rh
                ON r.uid = rh.recipe_id
            WHERE
                r.created IS NOT NULL
                AND r.created > %s
                AND rh.kind_id IS NOT NULL
                AND r.style_id IN ({})
            GROUP BY date(r.created, 'start of month'), rh.kind_id
        '''.format(','.join('%s' for _ in style_ids))

    per_month = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH] + style_ids)
    per_month = per_month.merge(recipes_per_month, on="month")
    per_month['month'] = pd.to_datetime(per_month['month'])
    per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes'] * 100

    trending = filter_trending(per_month, 'kind_id', 'month', 'recipes_percent')
    trending = set_multiple_series_start(trending, 'kind_id', 'month', 'recipes_percent')

    # Finally, add hop names
    trending['hop'] = trending['kind_id'].map(get_hop_names_dict())

    return trending
