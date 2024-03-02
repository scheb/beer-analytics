import tqdm
from django.core.management.base import BaseCommand
from elasticsearch.helpers import streaming_bulk

from recipe_db.models import SearchIndexUpdateQueue
from recipe_db.search.elasticsearch import get_elasticsearch, RECIPES_INDEX_NAME
from recipe_db.search.recipe_index import get_recipes_bulk_updates


class Command(BaseCommand):
    help = "Refresh recipe data in Elasticsearch"

    def add_arguments(self, parser):
        parser.add_argument("--forcemerge", action="store_true", help="Force merge after update")

    def handle(self, *args, **options) -> None:
        es = get_elasticsearch()

        # Process updates
        self.stdout.write("Bulk load updates")
        num_updates = SearchIndexUpdateQueue.objects.filter(index=RECIPES_INDEX_NAME).count()

        successes = 0
        progress = tqdm.tqdm(unit="docs", total=num_updates)
        for ok, action in streaming_bulk(es, actions=get_recipes_bulk_updates()):
            progress.update(1)
            successes += ok

        progress.close()
        self.stdout.write(f"Indexed {successes}/{num_updates} documents")

        # Optimize index
        if options["forcemerge"]:
            self.stdout.write("Force merge index")
            es.indices.forcemerge(index=RECIPES_INDEX_NAME)

        self.stdout.write("Refreshing index")
        es.indices.refresh(index=RECIPES_INDEX_NAME)
