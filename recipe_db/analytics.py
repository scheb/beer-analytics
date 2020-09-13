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
    df = df[df['style'].isin(style_ids)]
    return df


def get_all_styles_popularity() -> DataFrame:
    query = '''
        SELECT
            strftime('%Y-%m', created) AS month,
            style_id AS style,
            count(uid) AS recipes
        FROM recipe_db_recipe
        WHERE
            created IS NOT NULL
            AND created > '2012-01-01'
            AND style_id IS NOT NULL
        GROUP BY strftime('%Y-%m', created), style_id
    '''

    df = pd.read_sql(query, connection)
    df['recipes_percent'] = 100 * df['recipes'] / df.groupby('month')['recipes'].transform('sum')
    return df


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


def get_style_popular_hops(style: Style) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()

    query = '''
        WITH recipe_hops_agg AS (
            SELECT recipe_id, kind_id, SUM(amount_percent) AS amount_percent
            FROM recipe_db_recipehop
            WHERE kind_id IS NOT NULL
            GROUP BY recipe_id, kind_id
        )
        SELECT rh.recipe_id, h.name AS hop, rh.amount_percent
        FROM recipe_hops_agg AS rh
        JOIN recipe_db_recipe AS r ON rh.recipe_id = r.uid
        JOIN recipe_db_hop AS h ON rh.kind_id = h.id
        WHERE r.style_id IN ({})
        '''.format(','.join('%s' for _ in style_ids))

    hops = pd.read_sql(query, connection, params=style_ids)

    top_hops_ids = hops["hop"].value_counts()[:10].index.values
    top_hops = hops[hops['hop'].isin(top_hops_ids)]  # Get only the values of the mostly used hops

    return top_hops


def get_style_popular_fermentables(style: Style) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()

    query = '''
        WITH recipe_fermentables_agg AS (
            SELECT recipe_id, kind_id, SUM(amount_percent) AS amount_percent
            FROM recipe_db_recipefermentable
            WHERE kind_id IS NOT NULL
            GROUP BY recipe_id, kind_id
        )
        SELECT rf.recipe_id, h.name AS fermentable, rf.amount_percent
        FROM recipe_fermentables_agg AS rf
        JOIN recipe_db_recipe AS r ON rf.recipe_id = r.uid
        JOIN recipe_db_fermentable AS h ON rf.kind_id = h.id
        WHERE r.style_id IN ({})
        '''.format(','.join('%s' for _ in style_ids))

    fermentables = pd.read_sql(query, connection, params=style_ids)

    top_fermentables_ids = fermentables["fermentable"].value_counts()[:10].index.values
    top_fermentables = fermentables[fermentables['fermentable'].isin(top_fermentables_ids)]  # Get only the values of the mostly used fermentable

    return top_fermentables


def get_style_hop_pairings(style: Style) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()

    query = '''
        WITH recipe_hops_agg AS (
            SELECT recipe_id, kind_id, SUM(amount_percent) AS amount_percent
            FROM recipe_db_recipehop
            WHERE kind_id IS NOT NULL
            GROUP BY recipe_id, kind_id
        )
        SELECT
            rh1.recipe_id,
            h1.name || ' + ' || h2.name AS pairing,
            h1.name AS hop1,
            rh1.amount_percent AS amount_percent1,
            h2.name AS hop2,
            rh2.amount_percent AS amount_percent2    FROM recipe_hops_agg AS rh1
        JOIN recipe_hops_agg AS rh2
            ON rh1.recipe_id = rh2.recipe_id AND rh1.kind_id < rh2.kind_id
        JOIN recipe_db_hop AS h1
            ON rh1.kind_id = h1.id
        JOIN recipe_db_hop AS h2
            ON rh2.kind_id = h2.id
        JOIN recipe_db_recipe AS r
            ON rh1.recipe_id = r.uid
        WHERE r.style_id IN ({})
    '''.format(','.join('%s' for _ in style_ids))

    pairings = pd.read_sql(query, connection, params=style_ids)

    # Filter top pairs
    top_pairings = pairings["pairing"].value_counts()[:5].index.values
    pairings = pairings[pairings['pairing'].isin(top_pairings)]

    # Merge the hops data from the 2 columns into a single list
    df1 = pairings[['pairing', 'hop1', 'amount_percent1']]
    df1.columns = ['pairing', 'hop', 'amount_percent']
    df2 = pairings[['pairing', 'hop2', 'amount_percent2']]
    df2.columns = ['pairing', 'hop', 'amount_percent']
    df = pd.concat([df1, df2])
    return df
