from django.apps import AppConfig
from django.contrib.staticfiles.apps import StaticFilesConfig


class WebAppConfig(AppConfig):
    name = "web_app"


class WebAppStaticFilesConfig(StaticFilesConfig):
    ignore_patterns = ["CVS", ".*", "*~", "LICENSE"]
