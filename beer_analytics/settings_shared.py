import structlog
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
    "django_structlog",
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
    "django_structlog.middlewares.RequestMiddleware",
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
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': env.str("DATABASE_NAME"),
        'USER': env.str("DATABASE_USER"),
        'PASSWORD': env.str("DATABASE_PASSWORD"),
        'HOST': env.str("DATABASE_HOST"),
        'PORT': '3306',
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json_formatter": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
            "foreign_pre_chain": [
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.format_exc_info,
                structlog.processors.StackInfoRenderer(),
            ],
        },
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": env.str("LOG_FILE"),
            "formatter": "json_formatter",
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

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

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

WEB_ANALYTICS_ROOT_URL = env.str("WEB_ANALYTICS_ROOT_URL", None)
WEB_ANALYTICS_SITE_ID = env.str("WEB_ANALYTICS_SITE_ID", None)
WEB_ANALYTICS_SCRIPT_NAME = "wa.js"
WEB_ANALYTICS_TRACKER_NAME = "t"

GOOGLE_API_CLIENT_CONFIG_FILE = env.str("GOOGLE_API_CLIENT_CONFIG_FILE", None)
