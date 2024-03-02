from django.db.models import Model

from recipe_db.models import Recipe, RecipeYeast, RecipeFermentable, RecipeHop, SearchIndexUpdateQueue
from recipe_db.search.recipe_index import queue_refresh_recipe_index


UPDATE = SearchIndexUpdateQueue.OPERATION_UPDATE
DELETE = SearchIndexUpdateQueue.OPERATION_DELETE


def entity_saved(sender: Model, instance: object, **kwargs) -> None:
    if isinstance(instance, Recipe):
        queue_refresh_recipe_index(UPDATE, instance)
        return

    affected_recipe = get_affected_recipe(instance)
    if affected_recipe:
        queue_refresh_recipe_index(UPDATE, affected_recipe)


def entity_deleted(sender: Model, instance: object, **kwargs) -> None:
    if isinstance(instance, Recipe):
        queue_refresh_recipe_index(DELETE, instance)
        return

    affected_recipe = get_affected_recipe(instance)
    if affected_recipe:
        queue_refresh_recipe_index(UPDATE, affected_recipe)


def get_affected_recipe(instance):
    if isinstance(instance, RecipeHop):
        return instance.recipe
    elif isinstance(instance, RecipeFermentable):
        return instance.recipe
    elif isinstance(instance, RecipeYeast):
        return instance.recipe

    return None
