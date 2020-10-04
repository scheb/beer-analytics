import math
from datetime import datetime
from typing import Tuple

import numpy as np
import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.models import Style, Hop, Fermentable, RecipeHop, Yeast

POPULARITY_MIN_MONTH = '2012-01-01'
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


def get_yeasts_percentiles() -> dict:
    df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_yeast', connection)
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
        SELECT date(created, 'start of month') AS month, count(uid) AS total_recipes
        FROM recipe_db_recipe
        WHERE created IS NOT NULL
        GROUP BY date(created, 'start of month')
        ORDER BY month ASC
    '''

    df = pd.read_sql(query, connection)
    df = df.set_index('month')

    return df


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


def filter_trending(df: DataFrame, series_column: str, time_column: str, value_column: str) -> DataFrame:
    # Take only last months
    num_months = 18
    start_date = pd.Timestamp('now').floor('D') - pd.offsets.MonthBegin(1) + pd.DateOffset(months=-num_months)

    # At least 10 days in the current month to take it into the calculation
    if datetime.now().day < 10:
        end_date = pd.Timestamp('now').floor('D') - pd.offsets.MonthBegin(1) + pd.DateOffset(days=-1)
    else:
        end_date = pd.Timestamp('now').floor('D')

    recent_df = df[df[time_column].between(start_date, end_date)]

    # Take only ones with minimum number of recipes == number of months
    recipes_per_series = recent_df.groupby(series_column)['recipes'].sum()
    recipes_per_series = recipes_per_series[recipes_per_series.gt(num_months)]
    recent_df = recent_df[recent_df[series_column].isin(recipes_per_series.index.values.tolist())]

    # Fill in missing months with 0
    series_ids = recent_df[series_column].unique()
    month_range = pd.date_range(start=recent_df[time_column].min(), end=recent_df[time_column].max(), freq='MS')
    new_index = pd.MultiIndex.from_product([series_ids, month_range], names=[series_column, time_column])
    zero_filled = recent_df.set_index([series_column, time_column])
    zero_filled = zero_filled.reindex(new_index, fill_value=0)

    slopes = zero_filled.groupby(series_column).agg({value_column: ['mean', slope]})
    slopes['slope_weighted'] = slopes[value_column]['slope'] / slopes[value_column]['mean']

    trending = slopes
    trending = trending[trending[value_column]['mean'] >= 0.3]  # At least 0.3% mean to be relevant
    trending = trending[trending['slope_weighted'] >= 0.8]  # At least weighted slope
    trending = trending.sort_values('slope_weighted', ascending=False)

    trending_ids = trending.reset_index()[series_column].values.tolist()[:10]
    return recent_df[recent_df[series_column].isin(trending_ids)]


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


def set_multiple_series_start(
    df: DataFrame,
    series_column: str,
    time_column: str,
    value_column: str
) -> DataFrame:
    series_dfs = []
    if len(df) == 0:
        return df

    series_values = df[series_column].unique()
    for series_value in series_values:
        series = df[df[series_column].eq(series_value)]
        series_dfs.append(set_series_start(series, time_column, value_column))

    return pd.concat(series_dfs)


def set_series_start(
    df: DataFrame,
    time_column: str,
    value_column: str
) -> DataFrame:
    time_indexed = df.set_index(pd.DatetimeIndex(df[time_column]))

    # Fill in missing months with NaN
    month_min = time_indexed.index.min()
    month_max = time_indexed.index.max()
    month_range = pd.date_range(start=month_min, end=month_max, freq='MS')
    time_indexed = time_indexed.reindex(month_range)

    # Find the minimum index first having 4/6 of values set in the rolling window
    rolling = time_indexed[value_column].rolling(9, min_periods=6).min().shift(-8)
    start_timestamp = rolling[rolling.notnull()].index.min()

    # No start date, return the original dataframe
    if start_timestamp is None:
        return df

    # Filter
    filtered = time_indexed[time_indexed.index >= start_timestamp]
    filtered = filtered[filtered[value_column].notnull()]

    return filtered.reset_index()


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
            date(r.created, 'start of month') AS month,
            fh.kind_id,
            f.name AS fermentable,
            count(DISTINCT r.uid) AS recipes
        FROM recipe_db_recipe AS r
        JOIN recipe_db_recipefermentable AS fh
            ON r.uid = fh.recipe_id
        JOIN recipe_db_fermentable AS f
            ON fh.kind_id = f.id
        WHERE
            r.created IS NOT NULL
            AND r.created > %s
            AND fh.kind_id = %s
        GROUP BY date(r.created, 'start of month'), fh.kind_id
    '''

    per_month = pd.read_sql(query, connection, params=[POPULARITY_MIN_MONTH, fermentable.id])
    per_month = per_month.merge(recipes_per_month, on="month")
    per_month['recipes_percent'] = per_month['recipes'] / per_month['total_recipes'] * 100

    per_month = set_series_start(per_month, 'month', 'recipes_percent')

    return per_month


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
            r.created IS NOT NULL
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


def load_all_recipe_yeasts_aggregated():
    df = pd.read_sql_query('SELECT * FROM recipe_db_recipeyeast', connection)

    # Aggregate per recipe
    df = df.groupby(["recipe_id", "kind_id"], as_index=False).last()
    df = df.reset_index()

    return df


def calculate_yeast_recipe_count(df, yeast: Yeast) -> int:
    return len(df[df['kind_id'].eq(yeast.id)]['recipe_id'].unique())


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


def lowerfence(x):
    return x.quantile(0.02)


def q1(x):
    return x.quantile(0.25)


def q3(x):
    return x.quantile(0.75)


def upperfence(x):
    return x.quantile(0.98)


def slope(d):
    if len(d) < 4:
        return 0
    return np.polyfit(np.linspace(0, 1, len(d)), d, 1)[0]
