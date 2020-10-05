import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import lowerfence, q1, q3, upperfence, POPULARITY_MIN_MONTH
from recipe_db.analytics.charts.style import get_num_recipes_per_style
from recipe_db.analytics.utils import get_hop_names_dict, get_style_names_dict, get_num_recipes_per_month, \
    set_multiple_series_start, set_series_start
from recipe_db.models import Style, Hop, RecipeHop


def get_style_popular_hops(style: Style, use_filter: list) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()

    query = '''
        SELECT rh.recipe_id, rh.kind_id, rh.amount_percent
        FROM recipe_db_recipehop AS rh
        JOIN recipe_db_recipe AS r ON rh.recipe_id = r.uid
        WHERE r.style_id IN ({})
        '''.format(','.join('%s' for _ in style_ids))

    if len(use_filter):
        query += " AND rh.use IN ({})".format(','.join('%s' for _ in use_filter))

    df = pd.read_sql(query, connection, params=style_ids + use_filter)
    if len(df) == 0:
        return df

    # Aggregate amount per recipe
    hops = df.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum"}).reset_index()

    # Filter top hops
    top_hops_ids = hops["kind_id"].value_counts()[:10].index.values
    top_hops = hops[hops['kind_id'].isin(top_hops_ids)]  # Get only the values of the mostly used hops

    # Calculate boxplot values
    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence, 'count']
    aggregated = top_hops.groupby('kind_id').agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()
    aggregated = aggregated.sort_values(by=('amount_percent', 'count'), ascending=False)

    # Finally, add hop names
    aggregated['hop'] = aggregated['kind_id'].map(get_hop_names_dict())

    return aggregated


def get_hop_amount_range(hop: Hop) -> DataFrame:
    # Pre-select only the hops used in recipes using that hop
    query = '''
        SELECT recipe_id, kind_id, amount_percent
        FROM recipe_db_recipehop
        WHERE kind_id = %s
    '''

    df = pd.read_sql(query, connection, params=[hop.id])

    # Aggregate amount per recipe
    hop_amounts = df.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum"}).reset_index()
    hop_amounts['style'] = 'All'

    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence]
    aggregated = hop_amounts.groupby('style').agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()

    return aggregated


def get_hop_amount_range_per_style(hop: Hop) -> DataFrame:
    # Pre-select only the hops used in recipes using that hop
    query = '''
        SELECT rh.recipe_id, r.style_id, rh.kind_id, rh.amount_percent
        FROM recipe_db_recipehop AS rh
        JOIN recipe_db_recipe AS r
            ON rh.recipe_id = r.uid
        WHERE rh.kind_id = %s AND r.style_id IS NOT NULL
    '''

    df = pd.read_sql(query, connection, params=[hop.id])

    # Aggregate amount per recipe
    amounts = df.groupby(["recipe_id", "style_id", "kind_id"]).agg({"amount_percent": "sum"}).reset_index()

    top_style_ids = amounts["style_id"].value_counts()[:16].index.values
    top_style_amounts = amounts[amounts['style_id'].isin(top_style_ids)]  # Get only the values of the mostly used fermentable

    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence, 'count']
    aggregated = top_style_amounts.groupby('style_id').agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()
    aggregated = aggregated.sort_values(by=('amount_percent', 'count'), ascending=False)

    # Finally, add style names
    aggregated['style'] = aggregated['style_id'].map(get_style_names_dict())

    return aggregated


def get_hop_amount_range_per_use(hop: Hop) -> DataFrame:
    # Pre-select only the hops used in recipes using that hop
    query = '''
        SELECT rh.recipe_id, rh.use AS use_id, rh.kind_id, rh.amount_percent
        FROM recipe_db_recipehop AS rh
        WHERE rh.kind_id = %s AND rh.use IS NOT NULL
    '''

    df = pd.read_sql(query, connection, params=[hop.id])

    # Aggregate amount per recipe
    amounts = df.groupby(["recipe_id", "use_id", "kind_id"]).agg({"amount_percent": "sum"}).reset_index()

    top_use_ids = amounts["use_id"].value_counts()[:16].index.values
    top_use_amounts = amounts[amounts['use_id'].isin(top_use_ids)]  # Get only the values of the mostly used fermentable

    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence]
    aggregated = top_use_amounts.groupby('use_id').agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()
    aggregated['use_id'] = pd.Categorical(aggregated['use_id'], categories=list(RecipeHop.get_uses().keys()), ordered=True)
    aggregated = aggregated.sort_values(by='use_id')

    # Finally, add use names
    aggregated['use'] = aggregated['use_id'].map(RecipeHop.get_uses())

    return aggregated


def get_hop_use_counts(hop: Hop) -> dict:
    results = connection.cursor().execute('''
        SELECT use, count(DISTINCT recipe_id) AS num_recipes
        FROM recipe_db_recipehop
        WHERE kind_id = %s AND use IS NOT NULL
        GROUP BY use
    ''', params=[hop.id])

    count_per_use = {}
    for result in results:
        (use, count) = result
        count_per_use[use] = count

    return count_per_use


def get_hop_usage(hop: Hop) -> DataFrame:
    return DataFrame(hop.use_count)



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


def get_most_popular_hops() -> DataFrame:
    recipes_per_month = get_num_recipes_per_month()

    query = '''
        SELECT
            date(r.created, 'start of month') AS month,
            rh.kind_id,
            h.name AS hop,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipehop AS rh
            ON r.uid = rh.recipe_id
        JOIN recipe_db_hop AS h
            ON rh.kind_id = h.id
        WHERE
            r.created IS NOT NULL
            AND r.created > %s
            AND rh.kind_id IS NOT NULL
        GROUP BY date(r.created, 'start of month'), rh.kind_id
    '''

    df = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH])
    df = df.merge(recipes_per_month, on="month")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100

    # Filter for the most popular since 2018
    recent = df[df['month'] > '2018-01']
    most_used = recent.groupby('kind_id').agg({"recipes_percent": "mean"}).sort_values('recipes_percent', ascending=False)[:8]
    most_used_kind_ids = most_used.index.values
    df = df[df['kind_id'].isin(most_used_kind_ids)]

    return df


def get_hops_popularity(hops: list) -> DataFrame:
    recipes_per_month = get_num_recipes_per_month()
    hop_ids = list(map(lambda x: x.id, hops))

    query = '''
        SELECT
            date(r.created, 'start of month') AS month,
            rh.kind_id,
            h.name AS hop,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipehop AS rh
            ON r.uid = rh.recipe_id
        JOIN recipe_db_hop AS h
            ON rh.kind_id = h.id
        WHERE
            r.created IS NOT NULL
            AND r.created > %s
            AND rh.kind_id IN ({})
        GROUP BY date(r.created, 'start of month'), rh.kind_id
    '''.format(','.join('%s' for _ in hop_ids))

    per_month = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH] + hop_ids)
    per_month = per_month.merge(recipes_per_month, on="month")
    per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes'] * 100

    per_month = set_multiple_series_start(per_month, 'kind_id', 'month', 'recipes_percent')

    return per_month


def get_hop_popularity(hop: Hop) -> DataFrame:
    recipes_per_month = get_num_recipes_per_month()

    query = '''
        SELECT
            date(r.created, 'start of month') AS month,
            rh.kind_id,
            h.name AS hop,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipehop AS rh
            ON r.uid = rh.recipe_id
        JOIN recipe_db_hop AS h
            ON rh.kind_id = h.id
        WHERE
            r.created IS NOT NULL
            AND r.created > %s
            AND rh.kind_id = %s
        GROUP BY date(r.created, 'start of month'), rh.kind_id
    '''

    per_month = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH, hop.id])
    per_month = per_month.merge(recipes_per_month, on="month")
    per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes'] * 100

    per_month = set_series_start(per_month, 'month', 'recipes_percent')

    return per_month


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
            r.created IS NOT NULL
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
