import tqdm

from itertools import chain
from typing import Iterable, Optional

from django.core.management.base import BaseCommand
from elasticsearch.helpers import streaming_bulk
from recipe_db.models import Recipe
from recipe_db.search.elasticsearch import get_elasticsearch, INDEX_NAME


class Command(BaseCommand):
    help = "Load recipe data into Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument("--limit", help="Number of records to load")
        parser.add_argument("--chunk_size", help="Chunk size", default=10000)
        parser.add_argument("--reset", action="store_true", help="Reset index")
        parser.add_argument("--forcemerge", action="store_true", help="Force merge after update")

    def handle(self, *args, **options) -> None:
        es = get_elasticsearch()

        # Reset the index
        reset = options["reset"]
        if reset:
            self.stdout.write("Delete old index")
            es.options(ignore_status=[400, 404]).indices.delete(index=INDEX_NAME)

        self.stdout.write("Bulk load recipes")
        limit = int(options["limit"]) if options["limit"] is not None else None
        chunk_size = options["chunk_size"]
        num_records = limit or Recipe.objects.count()
        successes = 0
        progress = tqdm.tqdm(unit="docs", total=num_records)

        for recipe in get_recipes(limit, chunk_size):
            print(recipe)

        for ok, action in streaming_bulk(es, index=INDEX_NAME, actions=get_recipes(limit, chunk_size)):
            progress.update(1)
            successes += ok
        progress.close()
        self.stdout.write(f"Indexed {successes}/{num_records} documents")

        if options["forcemerge"]:
            self.stdout.write("Force merge index")
            es.indices.forcemerge(index=INDEX_NAME)

        self.stdout.write("Refreshing index")
        es.indices.refresh(index=INDEX_NAME)


def flat_list(values) -> list:
    return list(chain.from_iterable(values))


def get_recipes(limit: Optional[int], chunk_size: int) -> Iterable:
    processed = 0

    last_uid = "0"
    while True:
        processed_in_chunk = 0
        recipes = Recipe.objects \
            .prefetch_related("associated_styles", "associated_fermentables", "associated_hops", "associated_yeasts") \
            .filter(uid__gt=last_uid) \
            .order_by('uid') \
            .all()[:chunk_size]

        for recipe in recipes:
            yield create_recipe_doc(recipe)
            last_uid = recipe.uid

            # End when the limit is reached
            processed_in_chunk += 1
            processed += 1
            if limit is not None and processed >= limit:
                return

        # No more recipes to process
        if processed_in_chunk < chunk_size:
            return

def create_recipe_doc(recipe: Recipe):
    styles = recipe.associated_styles.all()
    hops = recipe.associated_hops.all()
    fermentables = recipe.associated_fermentables.all()
    yeasts = recipe.associated_yeasts.all()
    return {
        '_id': recipe.uid,
        '_source': {
            'name': recipe.name,
            'author': recipe.author,
            'created': recipe.created,
            'style_raw': recipe.style_raw,
            'style_names': flat_list(map(lambda x: x.all_names, styles)),
            'style_ids': list(set(map(lambda x: x.id, styles))),
            'ibu': recipe.ibu,
            'abv': recipe.abv,
            'srm': recipe.srm,
            'ebc': recipe.ebc,
            'og': recipe.og,
            'fg': recipe.fg,
            'hops': flat_list(map(lambda x: x.all_names, hops)),
            'hop_ids': list(set(map(lambda x: x.id, hops))),
            'fermentables': flat_list(map(lambda x: x.all_names, fermentables)),
            'fermentable_ids': list(set(map(lambda x: x.id, fermentables))),
            'yeasts': flat_list(map(lambda x: x.all_names, yeasts)),
            'yeast_ids': list(set(map(lambda x: x.id, yeasts))),
        }
    }
