# Per default load dev settings
try:
    from beer_analytics.settings_dev import *
except ImportError:
    pass
