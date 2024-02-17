import pprint

from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch

INDEX_NAME = 'recipes'

class Command(BaseCommand):
    help = "Search data in elasticsearch"

    def handle(self, *args, **options) -> None:
        es = Elasticsearch(
            "http://es:9200",
            basic_auth=("elastic", settings.__getattr__("ELASTICSEARCH_PASSWORD"))
        )

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
