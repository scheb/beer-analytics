from typing import Iterable

from django.conf import settings
from elastic_transport import ObjectApiResponse

from elasticsearch import Elasticsearch
from recipe_db.models import Recipe

SEARCHABLE_TEXT_FIELDS = ["name", "author", "style_raw", "style_names", "hops", "fermentables", "yeasts"]
INDEX_NAME = 'recipes'
RESULT_SIZE = 100

ELASTICSEARCH = Elasticsearch(
    "http://es:9200",
    basic_auth=("elastic", settings.__getattr__("ELASTICSEARCH_PASSWORD"))
)


class RecipeSearchResult:
    def __init__(self, result: ObjectApiResponse):
        self.hits = result[('hits')]['total']['value']
        self.hits_accurate = result['hits']['total']['relation'] == 'eq'
        self._result = result['hits']['hits']
        super().__init__()

    @property
    def recipes(self) -> Iterable[Recipe]:
        ids = map(lambda r: r['_id'], self._result)
        return Recipe.objects.filter(uid__in=ids)


def search_by_term(term: str):
    result = ELASTICSEARCH.search(
        index=INDEX_NAME,
        _source=False,
        size=RESULT_SIZE,
        query={
            'multi_match': {
                "query": term,
                "fields": SEARCHABLE_TEXT_FIELDS,
            },
        }
    )
    return RecipeSearchResult(result)
