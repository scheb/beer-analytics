import pandas as pd
from django.db import connection

from recipe_db.models import Yeast


def load_all_recipe_yeasts_aggregated():
    df = pd.read_sql_query('SELECT * FROM recipe_db_recipeyeast', connection)

    # Aggregate per recipe
    df = df.groupby(["recipe_id", "kind_id"], as_index=False).last()
    df = df.reset_index()

    return df


def calculate_yeast_recipe_count(df, yeast: Yeast) -> int:
    return len(df[df['kind_id'].eq(yeast.id)]['recipe_id'].unique())


def get_yeasts_percentiles() -> dict:
    df = pd.read_sql_query('SELECT id, recipes_count FROM recipe_db_yeast', connection)
    df['percentile'] = df['recipes_count'].rank(pct=True)
    return df.set_index('id').to_dict('index')
