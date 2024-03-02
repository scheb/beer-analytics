from django.apps import AppConfig

class RecipeDbConfig(AppConfig):
    name = "recipe_db"

    def ready(self):
        from django.db.models.signals import post_save, post_delete
        from recipe_db.search.signals import entity_saved, entity_deleted
        post_save.connect(entity_saved)
        post_delete.connect(entity_deleted)
