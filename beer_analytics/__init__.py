class DataImportRouter:
    route_app_labels = {"data_import"}

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "data_import"
        return "default"

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return "data_import"
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        return (obj1._meta.app_label in self.route_app_labels) == (obj2._meta.app_label in self.route_app_labels)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == "data_import"
        else:
            return db == "default"
