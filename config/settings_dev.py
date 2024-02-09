try:
    from config.settings_shared import *
except ImportError:
    pass

DEBUG = True

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "data": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "images": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
}
