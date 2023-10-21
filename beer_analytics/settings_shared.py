import json
from os import path
from pathlib import Path

from environ import Env

from web_app import DEFAULT_PAGE_CACHE_TIME

env = Env()
env.read_env()

BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

SECRET_KEY = env.str("SECRET_KEY")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
DEBUG = True

INSTALLED_APPS = [
    "recipe_db.apps.RecipeDbConfig",
    "web_app.apps.WebAppConfig",
    "django.contrib.humanize",
    "django.contrib.sites",
    "web_app.apps.WebAppStaticFilesConfig",
    "meta",
]

try:
    import data_import

    INSTALLED_APPS.append("data_import.apps.DataImportConfig")
except ModuleNotFoundError:
    pass

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "beer_analytics.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "beer_analytics.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "var/beer_analytics.sqlite3",
    },
    "data_import": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "var/data_import.sqlite3",
    },
}
DATABASE_ROUTERS = ["beer_analytics.DataImportRouter"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": env.str("LOG_FILE"),
        },
    },
    "root": {
        "handlers": ["file"],
        "level": env.str("LOG_LEVEL"),
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "level": env.str("LOG_LEVEL"),
            "propagate": False,
        },
    },
}

CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = DEFAULT_PAGE_CACHE_TIME
CACHE_MIDDLEWARE_KEY_PREFIX = ""

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_L10N = True
USE_TZ = False
USE_THOUSAND_SEPARATOR = True
NUMBER_GROUPING = 3

STATIC_URL = "/static/"
STATIC_ROOT = "static"
STATICFILES_DIRS = (path.join(BASE_DIR, "bundles"),)
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"

META_SITE_PROTOCOL = "https"
META_SITE_DOMAIN = "www.beer-analytics.com"
META_SITE_NAME = "Beer Analytics"
META_SITE_TYPE = "website"
META_INCLUDE_KEYWORDS = ["beer", "brewing", "recipe", "ingredients", "analysis", "analytics"]
META_USE_OG_PROPERTIES = True
META_USE_TWITTER_PROPERTIES = True
META_USE_TITLE_TAG = True
META_DEFAULT_IMAGE = "img/og.png"

RAW_DATA_DIR = env.str("RAW_DATA_DIR")
SOURCE_URL_PATTERNS = json.loads(env.str("SOURCE_URL_PATTERNS"))
