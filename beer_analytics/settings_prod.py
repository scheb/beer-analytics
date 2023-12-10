try:
    from beer_analytics.settings_shared import *
except ImportError:
    pass

DEBUG = False

NUM_ENTITIES = 1500
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": path.join(env.str("CACHE_DIR"), "default"),
        "OPTIONS": {"MAX_ENTRIES": 3 * NUM_ENTITIES},
    },
    "data": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": path.join(env.str("CACHE_DIR"), "data"),
        "OPTIONS": {"MAX_ENTRIES": 3 * NUM_ENTITIES * 10},
     },
    "images": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": path.join(env.str("CACHE_DIR"), "images")},
        "OPTIONS": {"MAX_ENTRIES": 3 * NUM_ENTITIES * 10},
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 2628000
