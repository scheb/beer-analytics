from typing import Tuple

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.models import Style, Hop, Fermentable


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


def load_all_recipe_hops():
    return pd.read_sql('SELECT * FROM recipe_db_recipehop', connection)


def calculate_hop_recipe_count(df, hop: Hop) -> int:
    return len(df[df['kind_id'].eq(hop.id)]['recipe_id'].unique())


def calculate_hop_metric(df, hop: Hop, metric: str) -> Tuple[float, float, float]:
    df = df[df['kind_id'].eq(hop.id)]
    df = remove_outliers(df, metric, 0.02)
    return df[metric].min(), df[metric].mean(), df[metric].max()


def load_all_recipe_fermentables():
    return pd.read_sql('SELECT * FROM recipe_db_recipefermentable', connection)


def calculate_fermentable_recipe_count(df, fermentable: Fermentable) -> int:
    return len(df[df['kind_id'].eq(fermentable.id)]['recipe_id'].unique())


def calculate_fermentable_metric(df, fermentable: Fermentable, metric: str) -> Tuple[float, float, float]:
    df = df[df['kind_id'].eq(fermentable.id)]
    df = remove_outliers(df, metric, 0.02)
    return df[metric].min(), df[metric].mean(), df[metric].max()


def remove_outliers(df: DataFrame, field: str, cutoff_percentile: float) -> DataFrame:
    lower_limit = df[field].quantile(cutoff_percentile)
    upper_limit = df[field].quantile(1.0 - cutoff_percentile)
    return df[df[field].between(lower_limit, upper_limit)]


def get_num_recipes_per_month() -> DataFrame:
    query = '''
        SELECT strftime('%Y-%m', created) AS month, count(uid) AS total_recipes
        FROM recipe_db_recipe
        GROUP BY strftime('%Y-%m', created)
        ORDER BY month ASC
    '''

    df = pd.read_sql(query, connection)
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
    recipes_per_month = get_num_recipes_per_month()

    query = '''
            SELECT
                strftime('%%Y-%%m', r.created) AS month,
                r.style_id,
                s.name AS style,
                count(r.uid) AS recipes
            FROM recipe_db_recipe AS r
            JOIN recipe_db_style AS s
                ON r.style_id = s.id
            WHERE
                created IS NOT NULL
                AND r.created > '2012-01-01'
                AND r.style_id IN ({})
            GROUP BY strftime('%%Y-%%m', r.created), r.style_id
        '''.format(','.join('%s' for _ in style_ids))

    df = pd.read_sql(query, connection, params=style_ids)
    df = df.set_index(['month', 'style_id'])
    df = df.merge(recipes_per_month, on="month")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
    df = df.reset_index()

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
            SELECT recipe_id, kind_id, sum(amount_percent) AS amount_percent
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

    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence, 'count']
    aggregated = top_hops.groupby('hop').agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()
    aggregated = aggregated.sort_values(by=('amount_percent', 'count'), ascending=False)

    return aggregated


def get_style_popular_fermentables(style: Style) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()

    query = '''
        WITH recipe_fermentables_agg AS (
            SELECT recipe_id, kind_id, sum(amount_percent) AS amount_percent
            FROM recipe_db_recipefermentable
            WHERE kind_id IS NOT NULL
            GROUP BY recipe_id, kind_id
        )
        SELECT f.name AS fermentable, rf.amount_percent
        FROM recipe_fermentables_agg AS rf
        JOIN recipe_db_recipe AS r ON rf.recipe_id = r.uid
        JOIN recipe_db_fermentable AS f ON rf.kind_id = f.id
        WHERE r.style_id IN ({})
        '''.format(','.join('%s' for _ in style_ids))

    fermentables = pd.read_sql(query, connection, params=style_ids)

    top_fermentables_ids = fermentables["fermentable"].value_counts()[:10].index.values
    top_fermentables = fermentables[fermentables['fermentable'].isin(top_fermentables_ids)]  # Get only the values of the mostly used fermentable

    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence, 'count']
    aggregated = top_fermentables.groupby('fermentable').agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()
    aggregated = aggregated.sort_values(by=('amount_percent', 'count'), ascending=False)

    return aggregated


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
    top_pairings = pairings["pairing"].value_counts()[:8].index.values
    pairings = pairings[pairings['pairing'].isin(top_pairings)]

    # Merge the hops data from the 2 columns into a single list
    df1 = pairings[['pairing', 'hop1', 'amount_percent1']]
    df1.columns = ['pairing', 'hop', 'amount_percent']
    df2 = pairings[['pairing', 'hop2', 'amount_percent2']]
    df2.columns = ['pairing', 'hop', 'amount_percent']
    df = pd.concat([df1, df2])

    # Sort by pairing popularity
    df['pairing'] = pd.Categorical(df['pairing'], top_pairings)
    df = df.sort_values(by=['pairing', 'hop'])
    df = df.reset_index()

    return df


def get_hop_popularity(hop: Hop) -> DataFrame:
    recipes_per_month = get_num_recipes_per_month()

    query = '''
        SELECT
            strftime('%%Y-%%m', r.created) AS month,
            rh.kind_id,
            h.name AS hop,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipehop AS rh
            ON r.uid = rh.recipe_id
        JOIN recipe_db_hop AS h
            ON rh.kind_id = h.id
        WHERE
            created IS NOT NULL
            AND r.created > '2012-01-01'
            AND rh.kind_id = %s
        GROUP BY strftime('%%Y-%%m', r.created), rh.kind_id
    '''

    df = pd.read_sql(query, connection, params=[hop.id])
    df = df.set_index(['month', 'kind_id'])
    df = df.merge(recipes_per_month, on="month")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
    df = df.reset_index()

    return df


def get_hop_common_styles(hop: Hop) -> DataFrame:
    recipes_per_style = get_num_recipes_per_style()

    query = '''
        SELECT
            r.style_id,
            s.name AS style_name,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipehop AS rh
            ON r.uid = rh.recipe_id
        JOIN recipe_db_style AS s
            ON r.style_id = s.id
        WHERE
            created IS NOT NULL
            AND r.created > '2012-01-01'
            AND rh.kind_id = %s
        GROUP BY r.style_id
    '''

    df = pd.read_sql(query, connection, params=[hop.id])
    df = df.set_index(['style_id'])
    df = df.merge(recipes_per_style, on="style_id")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
    df = df.sort_values('recipes_percent', ascending=False)
    df = df[:30]
    df = df.reset_index()

    return df


def get_fermentable_popularity(fermentable: Fermentable) -> DataFrame:
    recipes_per_month = get_num_recipes_per_month()

    query = '''
        SELECT
            strftime('%%Y-%%m', r.created) AS month,
            fh.kind_id,
            f.name AS fermentable,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipefermentable AS fh
            ON r.uid = fh.recipe_id
        JOIN recipe_db_fermentable AS f
            ON fh.kind_id = f.id
        WHERE
            created IS NOT NULL
            AND r.created > '2012-01-01'
            AND fh.kind_id = %s
        GROUP BY strftime('%%Y-%%m', r.created), fh.kind_id
    '''

    df = pd.read_sql(query, connection, params=[fermentable.id])
    df = df.set_index(['month', 'kind_id'])
    df = df.merge(recipes_per_month, on="month")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
    df = df.reset_index()

    return df


def get_fermentable_common_styles(fermentable: Fermentable) -> DataFrame:
    recipes_per_style = get_num_recipes_per_style()

    query = '''
        SELECT
            r.style_id,
            s.name AS style_name,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipefermentable AS rf
            ON r.uid = rf.recipe_id
        JOIN recipe_db_style AS s
            ON r.style_id = s.id
        WHERE
            created IS NOT NULL
            AND r.created > '2012-01-01'
            AND rf.kind_id = %s
        GROUP BY r.style_id
    '''

    df = pd.read_sql(query, connection, params=[fermentable.id])
    df = df.set_index(['style_id'])
    df = df.merge(recipes_per_style, on="style_id")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
    df = df.sort_values('recipes_percent', ascending=False)
    df = df[:30]
    df = df.reset_index()

    return df


def lowerfence(x):
    return x.quantile(0.02)


def q1(x):
    return x.quantile(0.25)


def q3(x):
    return x.quantile(0.75)


def upperfence(x):
    return x.quantile(0.98)
