try:
    from beer_analytics.settings_shared import *
except ImportError:
    pass

DEBUG = False

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.filebased.FileBasedCache", "LOCATION": path.join(env.str("CACHE_DIR"), "default")},
    "data": {"BACKEND": "django.core.cache.backends.filebased.FileBasedCache", "LOCATION": path.join(env.str("CACHE_DIR"), "data")},
    "images": {"BACKEND": "django.core.cache.backends.filebased.FileBasedCache", "LOCATION": path.join(env.str("CACHE_DIR"), "images")},
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 2628000
