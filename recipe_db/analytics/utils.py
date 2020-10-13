from datetime import datetime

import pandas as pd
from django.db import connection
from pandas import DataFrame

from recipe_db.analytics import slope
from recipe_db.models import Yeast


def get_style_names_dict() -> dict:
    return dict(connection.cursor().execute("SELECT id, name FROM recipe_db_style"))


def get_fermentable_names_dict() -> dict:
    return dict(connection.cursor().execute("SELECT id, name FROM recipe_db_fermentable"))


def get_hop_names_dict() -> dict:
    return dict(connection.cursor().execute("SELECT id, name FROM recipe_db_hop"))


def get_yeast_names_dict() -> dict:
    yeast_names = {}
    for yeast in Yeast.objects.all():
        product_name = yeast.full_name
        if yeast.has_extra_product_id:
            product_name += " ("+yeast.product_id+")"
        yeast_names[yeast.id] = product_name
    return yeast_names


def remove_outliers(df: DataFrame, field: str, cutoff_percentile: float) -> DataFrame:
    lower_limit = df[field].quantile(cutoff_percentile)
    upper_limit = df[field].quantile(1.0 - cutoff_percentile)
    return df[df[field].between(lower_limit, upper_limit)]


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
    if len(df) == 0:
        return df

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
