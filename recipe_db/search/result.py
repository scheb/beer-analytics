from typing import Optional

from recipe_db.models import SourceInfo, Recipe


class RecipeResultBuilder:
    def __init__(self):
        self.sources = {}
        for source in SourceInfo.objects.all():
            self.sources[source.source_id] = source

    def create_recipe_result(self, recipe: Recipe):
        source = None
        if recipe.source in self.sources:
            source = self.sources[recipe.source]
        return RecipeResult(recipe, source)


class RecipeResult:
    def __init__(self, recipe: Recipe, source: Optional[SourceInfo]):
        super().__init__()
        self._recipe = recipe
        self.source = source

    def __getattr__(self, key):
        return self._recipe.__getattribute__(key)

    @property
    def name(self):
        name = self._recipe.__getattribute__("name")
        return "Unnamed recipe" if name is None else name

    @property
    def url(self):
        if self.source is not None and self.source.recipe_url is not None:
            return self.source.recipe_url.format(self._recipe.source_id)
        return None
