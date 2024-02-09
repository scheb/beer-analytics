# Per default load dev settings
try:
    from config.settings_dev import *
except ImportError:
    pass
