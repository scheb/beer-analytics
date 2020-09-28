from typing import Tuple

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.models import Style, Hop, Fermentable, RecipeHop

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


def get_style_percentiles() -> dict:
    df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_style', connection)
    df['percentile'] = df['recipes_count'].rank(pct=True)
    return df.set_index('id').to_dict('index')


def get_hops_percentiles() -> dict:
    df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_hop', connection)
    df['percentile'] = df['recipes_count'].rank(pct=True)
    return df.set_index('id').to_dict('index')


def get_fermentables_percentiles() -> dict:
    df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_fermentable', connection)
    df['percentile'] = df['recipes_count'].rank(pct=True)
    return df.set_index('id').to_dict('index')


def get_hop_names_dict() -> dict:
    return dict(connection.cursor().execute("SELECT id, name FROM recipe_db_hop"))


def get_fermentable_names_dict() -> dict:
    return dict(connection.cursor().execute("SELECT id, name FROM recipe_db_fermentable"))


def get_style_names_dict() -> dict:
    return dict(connection.cursor().execute("SELECT id, name FROM recipe_db_style"))


def calculate_style_recipe_count(df, style: Style) -> int:
    style_ids = style.get_ids_including_sub_styles()
    return len(df[df['style_id'].isin(style_ids)])


def calculate_style_metric(df, style: Style, metric: str) -> Tuple[float, float, float]:
    style_ids = style.get_ids_including_sub_styles()
    df = df[df['style_id'].isin(style_ids)]
    return lowerfence(df[metric]), df[metric].median(), upperfence(df[metric])


def load_all_recipe_hops_aggregated():
    df = pd.read_sql_query('SELECT * FROM recipe_db_recipehop', connection)

    # Aggregate per recipe
    df = df.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum", "alpha": "mean"}).reset_index()
    df = df.reset_index()

    return df


def calculate_hop_recipe_count(df, hop: Hop) -> int:
    return len(df[df['kind_id'].eq(hop.id)]['recipe_id'].unique())


def calculate_hop_metric(df, hop: Hop, metric: str) -> Tuple[float, float, float]:
    df = df[df['kind_id'].eq(hop.id)]
    return lowerfence(df[metric]), df[metric].median(), upperfence(df[metric])


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
    return calculate_styles_popularity(style_ids)


def get_styles_popularity(styles: list) -> DataFrame:
    style_ids = list(map(lambda x: x.id, styles))
    return calculate_styles_popularity(style_ids)


def calculate_styles_popularity(style_ids: list) -> DataFrame:
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


def get_style_popular_fermentables(style: Style, category_filter: list, type_filter: list) -> DataFrame:
    style_ids = style.get_ids_including_sub_styles()

    query = '''
        SELECT rf.recipe_id, f.name AS fermentable, rf.amount_percent
        FROM recipe_db_recipefermentable AS rf
        JOIN recipe_db_recipe AS r ON rf.recipe_id = r.uid
        JOIN recipe_db_fermentable AS f ON rf.kind_id = f.id
        WHERE r.style_id IN ({})
        '''.format(','.join('%s' for _ in style_ids))

    if len(category_filter):
        query += " AND f.category IN ({})".format(','.join('%s' for _ in category_filter))
    if len(type_filter):
        query += " AND f.type IN ({})".format(','.join('%s' for _ in type_filter))

    df = pd.read_sql(query, connection, params=style_ids + category_filter + type_filter)
    if len(df) == 0:
        return df

    # Aggregate amount per recipe
    fermentables = df.groupby(["recipe_id", "fermentable"]).agg({"amount_percent": "sum"}).reset_index()

    top_fermentables_ids = fermentables["fermentable"].value_counts()[:10].index.values
    top_fermentables = fermentables[fermentables['fermentable'].isin(top_fermentables_ids)]  # Get only the values of the mostly used fermentable

    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence, 'count']
    aggregated = top_fermentables.groupby('fermentable').agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()
    aggregated = aggregated.sort_values(by=('amount_percent', 'count'), ascending=False)

    return aggregated


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
            strftime('%Y-%m', r.created) AS month,
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
            AND rh.kind_id IS NOT NULL
        GROUP BY strftime('%Y-%m', r.created), rh.kind_id
    '''

    df = pd.read_sql(query, connection)
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
            AND rh.kind_id IN ({})
        GROUP BY strftime('%%Y-%%m', r.created), rh.kind_id
    '''.format(','.join('%s' for _ in hop_ids))

    df = pd.read_sql(query, connection, params=hop_ids)
    df = df.set_index(['month', 'kind_id'])
    df = df.merge(recipes_per_month, on="month")
    df['recipes_percent'] = df['recipes'] / df['total_recipes'] * 100
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


def get_fermentable_amount_range(fermentable: Fermentable) -> DataFrame:
    # Pre-select only the hops used in recipes using that hop
    query = '''
        SELECT recipe_id, kind_id, amount_percent
        FROM recipe_db_recipefermentable
        WHERE kind_id = %s
    '''

    df = pd.read_sql(query, connection, params=[fermentable.id])

    # Aggregate amount per recipe
    hop_amounts = df.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum"}).reset_index()
    hop_amounts['style'] = 'All'

    agg = [lowerfence, q1, 'median', 'mean', q3, upperfence]
    aggregated = hop_amounts.groupby('style').agg({'amount_percent': agg})
    aggregated = aggregated.reset_index()

    return aggregated


def get_fermentable_amount_range_per_style(fermentable: Fermentable) -> DataFrame:
    # Pre-select only the fermentables used in recipes using that fermentable
    query = '''
        SELECT rf.recipe_id, r.style_id, rf.kind_id, rf.amount_percent
        FROM recipe_db_recipefermentable AS rf
        JOIN recipe_db_recipe AS r
            ON rf.recipe_id = r.uid
        WHERE rf.kind_id = %s AND r.style_id IS NOT NULL
    '''

    df = pd.read_sql(query, connection, params=[fermentable.id])

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


def get_fermentable_pairing_fermentables(fermentable: Fermentable) -> DataFrame:
    fermentable_id = fermentable.id

    # Pre-select only the hops used in recipes using that hop
    query = '''
        SELECT recipe_id, kind_id, amount_percent
        FROM recipe_db_recipefermentable
        WHERE recipe_id IN (
            SELECT DISTINCT recipe_id
            FROM recipe_db_recipefermentable
            WHERE kind_id = %s
        )
    '''

    fermentables = pd.read_sql(query, connection, params=[fermentable_id])
    return get_fermentable_pairings(fermentables, pair_must_include=fermentable)


def get_fermentable_pairings(fermentables: DataFrame, pair_must_include: Fermentable = None) -> DataFrame:
    # Aggregate amount per recipe
    fermentables = fermentables.groupby(["recipe_id", "kind_id"]).agg({"amount_percent": "sum"}).reset_index()

    # Create unique pairs per recipe
    pairs = pd.merge(fermentables, fermentables, on='recipe_id', suffixes=('_1', '_2'))
    pairs = pairs[pairs['kind_id_1'] < pairs['kind_id_2']]
    if pair_must_include is not None:
        pairs = pairs[pairs['kind_id_1'].eq(pair_must_include.id) | pairs['kind_id_2'].eq(pair_must_include.id)]
    pairs['pairing'] = pairs['kind_id_1'] + " " + pairs['kind_id_2']

    # Filter only the top pairs
    top_pairings = pairs["pairing"].value_counts()[:8].index.values
    pairs = pairs[pairs['pairing'].isin(top_pairings)]

    # Merge left and right fermentable into one dataset
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

    # Finally, add fermentable names
    aggregated['fermentable'] = aggregated['kind_id'].map(get_fermentable_names_dict())

    return aggregated


def lowerfence(x):
    return x.quantile(0.02)


def q1(x):
    return x.quantile(0.25)


def q3(x):
    return x.quantile(0.75)


def upperfence(x):
    return x.quantile(0.98)
