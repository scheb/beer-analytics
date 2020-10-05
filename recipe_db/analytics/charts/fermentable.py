import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import lowerfence, q1, q3, upperfence, POPULARITY_MIN_MONTH
from recipe_db.analytics.charts.style import get_num_recipes_per_style
from recipe_db.analytics.utils import get_style_names_dict, get_num_recipes_per_month, set_series_start
from recipe_db.models import Style, Fermentable


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
