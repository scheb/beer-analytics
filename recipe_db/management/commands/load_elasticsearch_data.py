import tqdm

from itertools import chain
from typing import Iterable

from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch
from elasticsearch.helpers import streaming_bulk
from recipe_db.models import Recipe

INDEX_NAME = 'recipes'

class Command(BaseCommand):
    help = "Load recipe data into Elasticsearch"

    def handle(self, *args, **options) -> None:
        es = Elasticsearch(
            "http://es:9200",
            basic_auth=("elastic", settings.__getattr__("ELASTICSEARCH_PASSWORD"))
        )

        # print(es.info())
        # self.stdout.write("Delete old index")
        # es.options(ignore_status=[400, 404]).indices.delete(index=INDEX_NAME)

        self.stdout.write("Bulk load recipes")
        limit = 10000
        successes = 0
        progress = tqdm.tqdm(unit="docs", total=limit)
        for ok, action in streaming_bulk(es, index=INDEX_NAME, actions=get_recipes(limit)):
            progress.update(1)
            successes += ok
        progress.close()
        self.stdout.write(f"Indexed {successes}/{limit} documents")

        self.stdout.write("Refreshing index")
        es.indices.forcemerge(index=INDEX_NAME)
        es.indices.refresh(index=INDEX_NAME)
        self.stdout.write("Done")
        # print(es.indices.stats(index=INDEX_NAME))

def flat_list(values) -> list:
    return list(chain.from_iterable(values))

def get_recipes(limit: int) -> Iterable:
    recipes = Recipe.objects \
                  .prefetch_related("associated_styles", "associated_fermentables", "associated_hops", "associated_yeasts") \
                  .all()[:limit]

    for recipe in recipes:
        styles = recipe.associated_styles.all()
        hops = recipe.associated_hops.all()
        fermentables = recipe.associated_fermentables.all()
        yeasts = recipe.associated_yeasts.all()
        yield {
            '_id': recipe.uid,
            '_source': {
                'name': recipe.name,
                'author': recipe.author,
                'created': recipe.created,
                'style_raw': recipe.style_raw,
                'style_names': flat_list(map(lambda x: x.all_names, styles)),
                'style_ids': flat_list(map(lambda x: x.id, styles)),
                'ibu': recipe.ibu,
                'abv': recipe.abv,
                'srm': recipe.srm,
                'ebc': recipe.ebc,
                'og': recipe.og,
                'fg': recipe.fg,
                'hops': flat_list(map(lambda x: x.all_names, hops)),
                'fermentables': flat_list(map(lambda x: x.all_names, fermentables)),
                'yeasts': flat_list(map(lambda x: x.all_names, yeasts)),
            }
        }
