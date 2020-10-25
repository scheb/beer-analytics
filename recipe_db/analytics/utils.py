import math
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


class RollingAverage:
    TIME_UNIT_MONTH = 'month'
    TIME_UNIT_DAY = 'day'

    def __init__(self, window: int = 7, time_unit: str = TIME_UNIT_MONTH) -> None:
        self.window = window
        self.min_data_points = math.floor(window / 2)
        self.time_freq = '1d' if time_unit == 'day' else 'MS'

    def rolling(self, df: DataFrame, time_column: str) -> DataFrame:
        if len(df) <= self.min_data_points:
            return DataFrame()

        df = df.set_index(time_column)
        df = df.set_index(pd.DatetimeIndex(df.index))

        # Fill in missing days with zeros

        # Pad in zeros on the left (half window width) to smoothen spikes at the beginning of a time series
        day_min = df.index.min() - pd.DateOffset(months=math.floor(self.window/2))
        day_max = df.index.max()
        day_range = pd.date_range(start=day_min, end=day_max, freq=self.time_freq, name=time_column)
        df = df.reindex(day_range, fill_value=0)

        # Rolling calculation
        rolling_df = df.rolling(self.window, min_periods=4, win_type='cosine', center=True).mean()

        # Find non-zero start
        start_timestamp = rolling_df[rolling_df > 0].index.min()
        filtered = rolling_df[rolling_df.index >= start_timestamp]
        filtered = filtered[filtered.notnull().any(axis=1)]
        filtered = filtered[filtered.index.day == 1]

        return filtered.reset_index()

    def rolling_multiple_series(self, df: DataFrame, series_column: str, time_column: str) -> DataFrame:
        if len(df) == 0:
            return df

        series_dfs = []
        series_values = df[series_column].unique()
        for series_value in series_values:
            series_df = df[df[series_column].eq(series_value)]
            series_df = series_df.drop([series_column], axis=1)
            rolling_series_df = self.rolling(series_df, time_column)
            if len(rolling_series_df) > 0:
                rolling_series_df[series_column] = series_value
                series_dfs.append(rolling_series_df)

        if len(series_dfs) == 0:
            dummy = DataFrame(columns=df.columns)
            return dummy

        return pd.concat(series_dfs)


class Trending:
    def __init__(self, smoothing: RollingAverage, trending_window: int = 12) -> None:
        self.smoothing = smoothing
        self.trending_window = trending_window

    def get_trending_series(self,
        df: DataFrame,
        series_column: str,
        time_column: str,
        percent_column: str,
        count_column: str
    ) -> list:
        df = self.smoothing.rolling_multiple_series(df, series_column, time_column)
        if len(df) == 0:
            return []

        # Look only at the last months
        max_time = max(df[time_column])
        start_time = pd.Timestamp('now').floor('D') - pd.offsets.MonthBegin(1) - pd.DateOffset(months=self.trending_window)

        # We have to be at least 10 days in the current month to take it into the calculation
        if datetime.now().day < 10:
            end_month = pd.Timestamp('now').floor('D') - pd.offsets.MonthBegin(1) + pd.DateOffset(days=-1)
        else:
            end_month = pd.Timestamp('now').floor('D') - pd.offsets.MonthBegin(1)

        # Slice out recent data
        recent_df = df[df[time_column].between(start_time, end_month)]
        if len(recent_df) == 0:
            return recent_df

        # Comparison time frame
        lookback_start_time = start_time - pd.DateOffset(months=self.trending_window * 2)
        lookback_df = df[df[time_column].between(lookback_start_time, start_time)]

        # Calculate mean and slope on recent time frame
        trend_df = recent_df.groupby(series_column).agg({percent_column: ['mean', slope], count_column: "sum", time_column: "max"})
        trend_df.columns = ['mean', 'slope', 'data_points', 'max_time']
        trend_df = trend_df[trend_df['max_time'].eq(max_time)]  # Consider only when there's data till the end
        trend_df = trend_df[trend_df['data_points'] > self.trending_window]  # At least one data point per time frame on average
        recent_series_ids = trend_df.index.unique()

        # Calculate mean on the older time frame
        lookback_df = lookback_df[lookback_df[series_column].isin(recent_series_ids)]
        lookback_mean = lookback_df.groupby(series_column)[percent_column].mean()
        lookback_mean.name = 'mean_baseline'
        lookback_mean = lookback_mean.reindex(recent_series_ids, fill_value=0)  # Make sure we have values for all series

        # Insert lookback_mean
        trend_df = trend_df.join(lookback_mean)
        trend_df['slope_weighted'] = trend_df['slope'] / trend_df['mean']

        # Filtering
        trending = trend_df
        trending = trending[trending['slope'] >= 0]  # Slope must be positive
        trending = trending[trending['mean'] >= 0.002]  # At least 0.2% mean in the recent time frame
        trending = trending[trending['mean'] >= trending['mean_baseline'] * 1.2]  # At least 20% increase in mean
        trending = trending[trending['slope_weighted'] >= 0.4]
        trending = trending.sort_values('slope_weighted', ascending=False)

        trending_ids = trending.reset_index()[series_column].values.tolist()[:10]
        return trending_ids
