try:
    from beer_analytics.settings_shared import *
except ImportError:
    pass

DEBUG = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}
