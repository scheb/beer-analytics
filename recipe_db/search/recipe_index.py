from itertools import chain
from typing import Optional, Iterable

from recipe_db.models import Recipe, SearchIndexUpdateQueue

RECIPES_INDEX_NAME = 'recipes'
CHUNK_SIZE = 10000


def queue_refresh_recipe_index(operation: str, recipe: Recipe) -> None:
    index_update = SearchIndexUpdateQueue()
    index_update.operation = operation
    index_update.index = RECIPES_INDEX_NAME
    index_update.entity_id = recipe.uid
    index_update.save()


def get_recipes_bulk_inserts(limit: Optional[int]) -> Iterable[dict]:
    processed = 0

    last_uid = "0"
    while True:
        processed_in_chunk = 0
        recipes = Recipe.objects \
            .prefetch_related("associated_styles", "associated_fermentables", "associated_hops", "associated_yeasts") \
            .filter(uid__gt=last_uid) \
            .order_by('uid') \
            .all()[:CHUNK_SIZE]

        for recipe in recipes:
            yield bulk_add_recipe_document(recipe)
            last_uid = recipe.uid

            # End when the limit is reached
            processed_in_chunk += 1
            processed += 1
            if limit is not None and processed >= limit:
                return

        # No more recipes to process
        if processed_in_chunk < CHUNK_SIZE:
            return


def get_recipes_bulk_updates() -> Iterable[dict]:
    updates = SearchIndexUpdateQueue.objects.filter(index=RECIPES_INDEX_NAME).order_by('updated_at')
    for update in updates:
        # Generate the bulk document for the Elasticsearch update
        if update.operation == SearchIndexUpdateQueue.OPERATION_DELETE:
            yield bulk_delete_recipe_document(update.entity_id)
        elif update.operation == SearchIndexUpdateQueue.OPERATION_UPDATE:
            recipe = (Recipe.objects
                      .prefetch_related("associated_styles", "associated_fermentables", "associated_hops", "associated_yeasts")
                      .get(pk=update.entity_id))
            yield bulk_add_recipe_document(recipe)
        else:
            continue

        # Update processed
        update.delete()


def bulk_delete_recipe_document(recipe_uid: str) -> dict:
    return {'delete': {'_index': RECIPES_INDEX_NAME, '_id': recipe_uid}}


def bulk_add_recipe_document(recipe: Recipe) -> dict:
    styles = recipe.associated_styles.all()
    hops = recipe.associated_hops.all()
    fermentables = recipe.associated_fermentables.all()
    yeasts = recipe.associated_yeasts.all()
    return {
        '_id': recipe.uid,
        '_index': RECIPES_INDEX_NAME,
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


def flat_list(values) -> list:
    return list(chain.from_iterable(values))
