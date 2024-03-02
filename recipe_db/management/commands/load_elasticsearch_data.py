import tqdm
from django.core.management.base import BaseCommand
from elasticsearch.helpers import streaming_bulk

from recipe_db.models import Recipe
from recipe_db.search.elasticsearch import get_elasticsearch, RECIPES_INDEX_NAME
from recipe_db.search.recipe_index import get_recipes_bulk_inserts


class Command(BaseCommand):
    help = "Load recipe data into Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument("--limit", help="Number of records to load")
        parser.add_argument("--reset", action="store_true", help="Reset index")
        parser.add_argument("--forcemerge", action="store_true", help="Force merge after update")

    def handle(self, *args, **options) -> None:
        es = get_elasticsearch()

        # Reset the index
        reset = options["reset"]
        if reset:
            self.stdout.write("Delete old index")
            es.options(ignore_status=[400, 404]).indices.delete(index=RECIPES_INDEX_NAME)

        # Execute updates
        self.stdout.write("Bulk load recipes")
        limit = int(options["limit"]) if options["limit"] is not None else None
        num_records = limit or Recipe.objects.count()
        successes = 0
        progress = tqdm.tqdm(unit="docs", total=num_records)

        for ok, action in streaming_bulk(es, actions=get_recipes_bulk_inserts(limit)):
            progress.update(1)
            successes += ok

        progress.close()
        self.stdout.write(f"Indexed {successes}/{num_records} documents")

        # Optimize index
        if options["forcemerge"]:
            self.stdout.write("Force merge index")
            es.indices.forcemerge(index=RECIPES_INDEX_NAME)

        self.stdout.write("Refreshing index")
        es.indices.refresh(index=RECIPES_INDEX_NAME)
