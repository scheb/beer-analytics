from typing import Iterable, Optional

from django.conf import settings
from elastic_transport import ObjectApiResponse

from elasticsearch import Elasticsearch
from recipe_db.models import Recipe
from recipe_db.search.result import RecipeResultBuilder

# We can boost ingredients fields
# SEARCHABLE_TEXT_FIELDS = ["name", "style_raw^2", "style_names^2", "hops^2", "fermentables", "yeasts^2"]

SEARCHABLE_TEXT_FIELDS = ["name", "style_raw", "style_names", "hops", "fermentables", "yeasts"]
INDEX_NAME = 'recipes'
RESULT_SIZE = 100
ELASTICSEARCH = None


def get_elasticsearch():
    global ELASTICSEARCH
    if ELASTICSEARCH is None:
        ELASTICSEARCH = Elasticsearch(
            settings.__getattr__("ELASTICSEARCH_URL"),
            basic_auth=("elastic", settings.__getattr__("ELASTICSEARCH_PASSWORD"))
        )
    return ELASTICSEARCH


class RecipeSearchResult:
    def __init__(self, result: ObjectApiResponse):
        self.hits = result[('hits')]['total']['value']
        self.hits_accuracy = result['hits']['total']['relation']
        self._result = result['hits']['hits']
        super().__init__()

    @property
    def recipes(self) -> Iterable[Recipe]:
        ids = map(lambda r: r['_id'], self._result)
        recipes = Recipe.objects.filter(uid__in=ids)
        builder = RecipeResultBuilder()
        for recipe in recipes:
            yield builder.create_recipe_result(recipe)


def execute_search(term: Optional[str], hops: Optional[str], styles: Optional[str]) -> RecipeSearchResult:
    criteria = []

    if term is not None:
        criteria.append({
            'multi_match': {
                'query': term,
                'fields': SEARCHABLE_TEXT_FIELDS,
            }
        })

    if hops is not None:
        criteria.append({
            'term': {
                'hop_ids.keyword': hops,
            }
        })

    if styles is not None:
        criteria.append({
            'term': {
                'style_ids.keyword': styles,
            }
        })

    if len(criteria) == 1:
        query = criteria[0]  # Single criteria query
    else:
        # AND query
        query = {
            "bool": {
                "must": criteria
            }
        }

    print(query)

    return search_query(query, RESULT_SIZE)


def search_query(query, limit: int) -> RecipeSearchResult:
    result = get_elasticsearch().search(
        index=INDEX_NAME,
        _source=False,
        size=limit,
        query=query,
    )
    return RecipeSearchResult(result)
