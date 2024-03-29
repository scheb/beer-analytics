import pprint

from django.core.management.base import BaseCommand
from recipe_db.search.elasticsearch import get_elasticsearch

INDEX_NAME = 'recipes'

class Command(BaseCommand):
    help = "Search data in elasticsearch"

    def handle(self, *args, **options) -> None:
        es = get_elasticsearch()
        result = es.search(
            index=INDEX_NAME,
            # query={
            #     'range': {"ibu": {
            #         "gte": 1,
            #         "lte": 200,
            #     }},
            # }
            query={
                'multi_match': {
                    "query": "weizen",
                    "fields": ["name", "author", "style_raw", "style_names"],
                },
            }
        )
        pp = pprint.PrettyPrinter(depth=1, indent=4)
        pp.pprint(result)
