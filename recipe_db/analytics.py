from typing import Tuple

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.models import Style, Hop, Fermentable

METRIC_PRECISION = {
    'default': 1,
    'abv': 1,
    'ibu': 1,
    'srm': 1,
    'og': 3,
    'fg': 3,
}


def load_all_recipes():
    return pd.read_sql('SELECT * FROM recipe_db_recipe', connection)

def get_hop_names_dict() -> dict:
    return dict(connection.cursor().execute("SELECT id, name FROM recipe_db_hop"))

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
    precision = METRIC_PRECISION[metric] if metric in METRIC_PRECISION else METRIC_PRECISION['default']

    query = '''
            SELECT round({}, {}) as {}
            FROM recipe_db_recipe
            WHERE {} IS NOT NULL AND style_id IN ({})
        '''.format(metric, precision, metric, metric, ','.join('%s' for _ in style_ids))

    df = pd.read_sql(query, connection, params=style_ids)
    df = remove_outliers(df, metric, 0.02)

    histogram = df.groupby([pd.cut(df[metric], 16, precision=precision)])[metric].agg(['count'])
    histogram = histogram.reset_index()
    histogram[metric] = histogram[metric].map(str)

    return histogram


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
        SELECT rh.recipe_id, rh.kind_id, rh.amount_percent
        FROM recipe_db_recipehop AS rh
        JOIN recipe_db_recipe AS r
            ON rh.recipe_id = r.uid
        WHERE rh.kind_id IS NOT NULL AND r.style_id IN ({})
    '''.format(','.join('%s' for _ in style_ids))

    hops = pd.read_sql(query, connection, params=style_ids)
    return get_hop_pairings(hops)


def get_hop_pairings(hops: DataFrame, pair_must_include: Hop = None) -> DataFrame:
    # Aggregate amount per recipe
    hops = hops.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum"}).reset_index()

    # Create unique pairs per recipe
    pairs = pd.merge(hops, hops, on='recipe_id', suffixes=('_1', '_2'))
    pairs = pairs[pairs['kind_id_1'] < pairs['kind_id_2']]
    if pair_must_include is not None:
        pairs = pairs[pairs['kind_id_1'].eq(pair_must_include.id) | pairs['kind_id_2'].eq(pair_must_include.id)]
    pairs['pairing'] = pairs['kind_id_1'] + " " + pairs['kind_id_2']

    # Filter only the top pairs
    top_pairings = pairs["pairing"].value_counts()[:8].index.values
    pairs = pairs[pairs['pairing'].isin(top_pairings)]

    # Merge left and right hop into one dataset
    df1 = pairs[['pairing', 'kind_id_1', 'amount_percent_1']]
    df1.columns = ['pairing', 'kind_id', 'amount_percent']
    df2 = pairs[['pairing', 'kind_id_2', 'amount_percent_2']]
    df2.columns = ['pairing', 'kind_id', 'amount_percent']
    top_pairings = pd.concat([df1, df2])

    # Calculate boxplot values
    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence, 'count']
    aggregated = top_pairings.groupby(['pairing', 'kind_id']).agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()
    aggregated = aggregated.sort_values(by=('amount_percent', 'count'), ascending=False)

    # Finally, add hop names
    aggregated['hop'] = aggregated['kind_id'].map(get_hop_names_dict())

    return aggregated


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


def get_hop_common_styles_absolute(hop: Hop) -> DataFrame:
    df = get_hop_common_styles_data(hop)

    df = df.sort_values('recipes', ascending=False)
    df = df[:30]

    return df


def get_hop_common_styles_relative(hop: Hop) -> DataFrame:
    recipes_per_style = get_num_recipes_per_style()
    df = get_hop_common_styles_data(hop)

    df = df.set_index(['style_id'])
    df = df.merge(recipes_per_style, on="style_id")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
    df = df.sort_values('recipes_percent', ascending=False)
    df = df[:30]
    df = df.reset_index()

    return df


def get_hop_common_styles_data(hop: Hop) -> DataFrame:
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

    return pd.read_sql(query, connection, params=[hop.id])


def get_hop_pairing_hops(hop: Hop) -> DataFrame:
    hop_id = hop.id

    # Pre-select only the hops used in recipes using that hop
    query = '''
        SELECT recipe_id, kind_id, amount_percent
        FROM recipe_db_recipehop
        WHERE recipe_id IN (
            SELECT DISTINCT recipe_id
            FROM recipe_db_recipehop
            WHERE kind_id = %s
        )
    '''

    hops = pd.read_sql(query, connection, params=[hop_id])
    return get_hop_pairings(hops, pair_must_include=hop)


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


def get_fermentable_common_styles_absolute(fermentable: Fermentable) -> DataFrame:
    df = get_fermentable_common_styles_data(fermentable)

    df = df.sort_values('recipes', ascending=False)
    df = df[:30]

    return df


def get_fermentable_common_styles_relative(fermentable: Fermentable) -> DataFrame:
    recipes_per_style = get_num_recipes_per_style()
    df = get_fermentable_common_styles_data(fermentable)

    df = df.set_index(['style_id'])
    df = df.merge(recipes_per_style, on="style_id")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
    df = df.sort_values('recipes_percent', ascending=False)
    df = df[:30]
    df = df.reset_index()

    return df


def get_fermentable_common_styles_data(fermentable: Fermentable) -> DataFrame:
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

    return pd.read_sql(query, connection, params=[fermentable.id])


def lowerfence(x):
    return x.quantile(0.02)


def q1(x):
    return x.quantile(0.25)


def q3(x):
    return x.quantile(0.75)


def upperfence(x):
    return x.quantile(0.98)
